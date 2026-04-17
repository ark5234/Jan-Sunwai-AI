"""
Workers router — Jan-Sunwai AI

Endpoints:
  Worker-facing:
    GET  /workers/me                          – own profile + active assignments
    PATCH /workers/me/status                  – toggle available / offline
    PATCH /workers/me/complaints/{id}/done    – mark one task done

  Admin-facing:
    GET  /workers                             – all workers (approved + pending)
    PATCH /workers/{id}/approve              – approve a pending registration
    DELETE /workers/{id}/reject              – reject & delete a pending registration
    POST  /workers/{id}/assign/{cid}         – manual override assignment
    PATCH /workers/{id}/area                 – update service area
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from app.auth import get_current_worker, get_current_admin, get_current_admin_or_dept_head
from app.database import get_database
from app.schemas import WorkerStatus, ServiceAreaUpdate, UserRole, ComplaintStatus
from app.services.assignment import free_worker_slot, _do_assign, auto_assign
from app.routers.notifications import create_notification
from app.schemas import NotificationType
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter()


def _fix(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ---------------------------------------------------------------------------
# Worker-facing
# ---------------------------------------------------------------------------

@router.get("/workers/me")
async def get_my_profile(current_user: dict = Depends(get_current_worker)):
    """Return own profile with active assignment details."""
    db = get_database()

    active_ids = current_user.get("active_complaint_ids", [])
    active_complaints = []
    for cid in active_ids:
        if ObjectId.is_valid(cid):
            doc = await db["complaints"].find_one({"_id": ObjectId(cid)})
            if doc:
                active_complaints.append(_fix(doc))

    # Resolved history (last 10)
    history_cursor = db["complaints"].find(
        {"assigned_to": str(current_user["_id"]), "status": ComplaintStatus.RESOLVED.value}
    ).sort("updated_at", -1).limit(10)
    history = [_fix(doc) async for doc in history_cursor]

    return {
        **current_user,
        "active_complaints": active_complaints,
        "resolved_history": history,
    }


@router.patch("/workers/me/status")
async def update_my_status(
    worker_status: WorkerStatus = Body(..., embed=True),
    current_user: dict = Depends(get_current_worker),
):
    """Toggle between available and offline. Busy is set automatically by assignment."""
    if worker_status == WorkerStatus.BUSY:
        raise HTTPException(
            status_code=400,
            detail="'busy' status is managed automatically by the assignment system."
        )
    db = get_database()
    await db["users"].update_one(
        {"_id": ObjectId(str(current_user["_id"]))},
        {"$set": {"worker_status": worker_status.value, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"message": f"Status updated to {worker_status.value}"}


@router.patch("/workers/me/complaints/{complaint_id}/done")
async def mark_task_done(
    complaint_id: str,
    current_user: dict = Depends(get_current_worker),
):
    """Mark one specific active complaint as Resolved and free that slot."""
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid complaint ID")

    db = get_database()
    worker_id = str(current_user["_id"])

    # Verify this complaint belongs to this worker
    if complaint_id not in current_user.get("active_complaint_ids", []):
        raise HTTPException(status_code=403, detail="This complaint is not in your active task list")

    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = complaint.get("status", ComplaintStatus.OPEN.value)

    # Resolve the complaint
    await db["complaints"].update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {"status": ComplaintStatus.RESOLVED.value, "updated_at": datetime.now(timezone.utc)},
            "$push": {
                "status_history": {
                    "status": ComplaintStatus.RESOLVED.value,
                    "timestamp": datetime.now(timezone.utc),
                    "changed_by_user_id": worker_id,
                    "note": "Marked as done by assigned field worker",
                }
            },
        },
    )

    # Notify the citizen
    citizen_id = complaint.get("user_id")
    if citizen_id:
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.STATUS_CHANGE,
            title="Grievance Resolved",
            message=f"Your grievance ({complaint.get('department', '')}) has been resolved by the field worker.",
            complaint_id=complaint_id,
            status_from=old_status,
            status_to=ComplaintStatus.RESOLVED.value,
        )

    # Free the slot and attempt re-assignment of queued complaints
    await free_worker_slot(worker_id, complaint_id, db)

    return {"message": "Complaint marked as resolved", "complaint_id": complaint_id}


# ---------------------------------------------------------------------------
# Admin-facing
# ---------------------------------------------------------------------------

@router.get("/workers/assignment-debug")
async def assignment_debug(
    current_user: dict = Depends(get_current_admin),
):
    """
    Diagnostic: shows unassigned complaints and eligible workers for each department.
    Helps pinpoint why auto-assignment is failing.
    """
    db = get_database()

    unassigned = []
    async for c in db["complaints"].find({
        "status": {"$in": [ComplaintStatus.OPEN.value, ComplaintStatus.IN_PROGRESS.value]},
        "$or": [{"assigned_to": None}, {"assigned_to": {"$exists": False}}],
    }).sort("created_at", 1):
        unassigned.append({
            "id": str(c["_id"]),
            "department": c.get("department"),
            "status": c.get("status"),
            "location": c.get("location"),
        })

    available_workers = []
    async for w in db["users"].find({"role": UserRole.WORKER.value, "is_approved": True}):
        available_workers.append({
            "id": str(w["_id"]),
            "username": w.get("username"),
            "department": w.get("department"),
            "worker_status": w.get("worker_status"),
            "is_approved": w.get("is_approved"),
            "service_area": w.get("service_area"),
            "active_task_count": len(w.get("active_complaint_ids", [])),
        })

    return {
        "unassigned_complaints": unassigned,
        "unassigned_count": len(unassigned),
        "available_workers": available_workers,
        "worker_count": len(available_workers),
    }


@router.post("/workers/reassign-unassigned")
async def reassign_unassigned(
    current_user: dict = Depends(get_current_admin),
):
    """
    Scan ALL Open + In-Progress unassigned complaints and attempt auto-assignment.
    Returns { assigned: N, skipped: M } where skipped = no eligible worker found.
    """
    db = get_database()

    # Include BOTH Open and In Progress complaints with no worker assigned
    cursor = db["complaints"].find(
        {
            "status": {"$in": [ComplaintStatus.OPEN.value, ComplaintStatus.IN_PROGRESS.value]},
            "$or": [{"assigned_to": None}, {"assigned_to": {"$exists": False}}],
        }
    ).sort("created_at", 1)

    assigned_count = 0
    skipped_count = 0

    async for complaint in cursor:
        cid = str(complaint["_id"])
        dept = complaint.get("department", "")
        loc = complaint.get("location")
        worker_id = await auto_assign(
            complaint_id=cid,
            department=dept,
            complaint_location=loc,
            db=db,
        )
        if worker_id:
            assigned_count += 1
            await create_notification(
                user_id=worker_id,
                notification_type=NotificationType.ASSIGNMENT,
                title="New Task Assigned",
                message=f"A new grievance has been assigned to you: {dept} — {complaint.get('description', '')[:80]}",
                complaint_id=cid,
            )
        else:
            skipped_count += 1

    return {
        "message": f"Re-assignment complete. Assigned: {assigned_count}, Skipped (no eligible worker): {skipped_count}.",
        "assigned": assigned_count,
        "skipped": skipped_count,
    }


@router.get("/workers")
async def list_workers(
    pending_only: bool = False,
    current_user: dict = Depends(get_current_admin),
):
    """List all workers. Set ?pending_only=true to see only unapproved registrations."""
    db = get_database()
    query: dict = {"role": UserRole.WORKER}
    if pending_only:
        query["is_approved"] = False

    workers = []
    async for worker in db["users"].find(query).sort("created_at", -1):
        w = _fix(worker)
        # Attach active complaint count
        w["active_task_count"] = len(w.get("active_complaint_ids", []))
        w.pop("password", None)  # Never leak passwords
        workers.append(w)
    return workers


@router.get("/workers/my-department")
async def list_workers_for_my_department(
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    """
    Return approved workers scoped to the caller's department.

    - DEPT_HEAD: only workers in their department.
    - ADMIN: all approved workers.
    """
    db = get_database()
    query: dict = {"role": UserRole.WORKER, "is_approved": True}

    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept:
            return []
        query["department"] = user_dept

    workers = []
    async for worker in db["users"].find(query).sort("created_at", -1):
        w = _fix(worker)
        w["active_task_count"] = len(w.get("active_complaint_ids", []))
        w.pop("password", None)
        workers.append(w)
    return workers


@router.patch("/workers/{worker_id}/approve")
async def approve_worker(
    worker_id: str,
    current_user: dict = Depends(get_current_admin),
):
    """Approve a pending worker registration."""
    if not ObjectId.is_valid(worker_id):
        raise HTTPException(status_code=400, detail="Invalid worker ID")

    db = get_database()
    worker = await db["users"].find_one({"_id": ObjectId(worker_id), "role": UserRole.WORKER})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if worker.get("is_approved"):
        raise HTTPException(status_code=409, detail="Worker is already approved")

    await db["users"].update_one(
        {"_id": ObjectId(worker_id)},
        {
            "$set": {
                "is_approved": True,
                "worker_status": WorkerStatus.AVAILABLE.value,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    # Notify the worker
    await create_notification(
        user_id=worker_id,
        notification_type=NotificationType.SYSTEM,
        title="Account Approved!",
        message="Your worker account has been approved by the admin. You can now log in and start accepting grievance assignments.",
        complaint_id=None,
    )

    return {"message": f"Worker {worker.get('username')} approved successfully"}


@router.delete("/workers/{worker_id}/reject")
async def reject_worker(
    worker_id: str,
    reason: str = Body(default="", embed=True),
    current_user: dict = Depends(get_current_admin),
):
    """Reject and permanently delete a pending worker registration."""
    if not ObjectId.is_valid(worker_id):
        raise HTTPException(status_code=400, detail="Invalid worker ID")

    db = get_database()
    worker = await db["users"].find_one({"_id": ObjectId(worker_id), "role": UserRole.WORKER})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if worker.get("is_approved"):
        raise HTTPException(status_code=409, detail="Cannot reject an already-approved worker. Deactivate instead.")

    await db["users"].delete_one({"_id": ObjectId(worker_id)})
    return {"message": f"Worker registration for '{worker.get('username')}' has been rejected and removed"}


@router.post("/workers/{worker_id}/assign/{complaint_id}")
async def manual_assign(
    worker_id: str,
    complaint_id: str,
    current_user: dict = Depends(get_current_admin),
):
    """Manually assign a complaint to a specific worker (admin override)."""
    if not ObjectId.is_valid(worker_id) or not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    worker = await db["users"].find_one(
        {"_id": ObjectId(worker_id), "role": UserRole.WORKER, "is_approved": True}
    )
    if not worker:
        raise HTTPException(status_code=404, detail="Approved worker not found")

    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    await _do_assign(db, worker, complaint_id)

    # Notify the worker about manual assignment
    await create_notification(
        user_id=worker_id,
        notification_type=NotificationType.ASSIGNMENT,
        title="New Task Assigned",
        message=f"Admin has manually assigned you a new grievance: {complaint.get('department', '')} — {complaint.get('description', '')[:80]}",
        complaint_id=complaint_id,
    )

    return {"message": "Complaint manually assigned", "worker_id": worker_id, "complaint_id": complaint_id}


@router.patch("/workers/{worker_id}/area")
async def update_service_area(
    worker_id: str,
    payload: ServiceAreaUpdate,
    current_user: dict = Depends(get_current_admin),
):
    """Update a worker's service area (admin only)."""
    if not ObjectId.is_valid(worker_id):
        raise HTTPException(status_code=400, detail="Invalid worker ID")

    db = get_database()
    result = await db["users"].update_one(
        {"_id": ObjectId(worker_id), "role": UserRole.WORKER},
        {"$set": {"service_area": payload.service_area.model_dump(), "updated_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Worker not found")

    return {"message": "Service area updated", "service_area": payload.service_area.model_dump()}
