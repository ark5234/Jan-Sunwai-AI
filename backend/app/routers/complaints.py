import asyncio
import csv
import io

from fastapi import APIRouter, File, UploadFile, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
from app.classifier import CivicClassifier
from app.geotagging import extract_location
from app.database import get_database
from app.services.storage import storage_service
from app.services.llm_queue import llm_queue_service
from app.auth import get_current_user, get_current_admin, get_current_admin_or_dept_head
from app.schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatus,
    TransferRequest,
    UserRole,
    FeedbackRequest,
    DeptNoteRequest,
    CommentRequest,
    BulkStatusUpdate,
    BulkTransfer,
    PriorityLevel,
)
from app.authorities import route_authority, get_authority_by_id
from app.routers.notifications import create_notification
from app.schemas import NotificationType
from app.config import settings
from app.services.priority import compute_priority
from PIL import Image
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter()
classifier = CivicClassifier()

# Helper to fix ObjectId serialization
def fix_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def await_generation(job_id: str, timeout_seconds: float) -> dict:
    elapsed = 0.0
    sleep_interval = 0.2
    while elapsed < timeout_seconds:
        result = llm_queue_service.get_result(job_id)
        if result and result.get("status") in ["completed", "failed"]:
            return result
        await asyncio.sleep(sleep_interval)
        elapsed += sleep_interval
    return {"status": "queued"}

@router.post("/analyze")
async def analyze_complaint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    username = current_user["username"]

    # 1. Save file and resolve absolute path
    file_path = await storage_service.save_file(file)
    absolute_file_path = storage_service.resolve_path(file_path)

    # 2. Classify — pass the saved file path to the Ollama pipeline
    classification = classifier.classify(absolute_file_path)

    # 3. Extract Location — open from the saved file on disk (avoids re-reading HTTP body)
    image = Image.open(absolute_file_path)
    location = extract_location(image)
    image.close()
    
    # 4. Generate Complaint Text (Async queue)
    # Only skip generation for images that are genuinely non-civic (selfie, food,
    # animal, train station, etc.) OR when the classifier itself errored out.
    # An image that the classifier couldn't categorise (Uncategorized) may still
    # be a real civic issue — generate a draft for it rather than hard-rejecting.
    is_truly_non_civic = (
        not classification.get("is_valid", True)
        and classification.get("is_non_civic", False)
    ) or classification.get("method") in ("non_civic_guard", "error")

    if not is_truly_non_civic:
        job_id = await llm_queue_service.enqueue(absolute_file_path, classification, {"name": username}, location)
        result = await await_generation(job_id, settings.llm_inline_timeout_seconds)
        if result.get("status") == "completed":
            generated_text = result.get("generated_complaint", "")
            generation_status = "completed"
        elif result.get("status") == "failed":
            generated_text = "AI draft failed. Please write complaint manually."
            generation_status = "failed"
        else:
            generated_text = "Complaint draft is being generated. Please refresh in a few seconds."
            generation_status = "queued"
    else:
        job_id = None
        generation_status = "skipped"
        if classification.get("method") == "error":
            generated_text = (
                "Image analysis failed — the AI model could not process this photo. "
                "Please try again or describe the issue manually below."
            )
        else:
            generated_text = (
                f"AI Analysis Result: {classification['label']}.\n\n"
                "This image does not appear to show a valid civic grievance relevant to municipal authorities. "
                "Please upload a photo of a civic issue (e.g., pothole, garbage, broken light) to generate a formal complaint."
            )
    
    return {
        "classification": classification,
        "location": location,
        "generated_complaint": generated_text,
        "generation_status": generation_status,
        "generation_job_id": job_id,
        "image_url": file_path # Return the path so frontend can pass it to /complaints
    }


@router.get("/complaints/generation/{job_id}")
async def get_generation_result(job_id: str, current_user: dict = Depends(get_current_user)):
    result = llm_queue_service.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return result


@router.post("/analyze/regenerate")
async def regenerate_complaint(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Re-run the complaint draft generator for an already-analysed image.
    Expects: { classification, location, image_url }
    Returns:  { job_id, status } — poll /complaints/generation/{job_id}
    """
    username = current_user["username"]
    classification = payload.get("classification", {})
    location       = payload.get("location", {})
    image_url      = payload.get("image_url", "")

    absolute_file_path = storage_service.resolve_path(image_url)

    job_id = await llm_queue_service.enqueue(
        absolute_file_path, classification, {"name": username}, location
    )
    return {"job_id": job_id, "status": "queued"}



@router.post("/complaints", response_model=ComplaintResponse)
async def create_complaint(
    complaint: ComplaintCreate, 
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    
    user_id = str(current_user["_id"])
    
    # 2. Prepare Data
    complaint_dict = complaint.model_dump()
    
    # Resolve Authority routing metadata
    routing = route_authority(complaint.department)

    # Compute AI-derived priority
    priority = compute_priority(
        complaint_dict.get("description", ""),
        complaint_dict.get("department", ""),
    )

    # Duplicate detection: same user + same department + similar location within 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    dup_query: dict = {
        "user_id": user_id,
        "department": complaint.department,
        "created_at": {"$gte": thirty_days_ago},
        "status": {"$nin": [ComplaintStatus.REJECTED]},
    }
    location_val = complaint_dict.get("location")
    if location_val:
        dup_query["location"] = location_val
    duplicate = await db["complaints"].find_one(dup_query)
    is_duplicate = bool(duplicate)

    complaint_dict.update({
        "user_id": user_id,
        "assigned_to": None,
        "authority_id": routing.get("authority_id"),
        "routing_confidence": routing.get("confidence"),
        "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
        "status": ComplaintStatus.OPEN,
        "priority": priority,
        "is_duplicate": is_duplicate,
        "duplicate_of": str(duplicate["_id"]) if is_duplicate else None,
        "escalated": False,
        "dept_notes": [],
        "comments": [],
        "feedback": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status_history": [{
            "status": ComplaintStatus.OPEN,
            "timestamp": datetime.utcnow(),
            "changed_by_user_id": user_id,
            "note": "Complaint created"
        }]
    })

    # 3. Insert into DB
    result = await db["complaints"].insert_one(complaint_dict)
    
    # 4. Notify citizen that complaint was filed
    complaint_dict["_id"] = str(result.inserted_id)
    await create_notification(
        user_id=user_id,
        notification_type=NotificationType.STATUS_CHANGE,
        title="Grievance Registered",
        message=f"Your grievance has been registered and routed to {complaint.department}. Current status: Open.",
        complaint_id=complaint_dict["_id"],
        status_from=None,
        status_to=ComplaintStatus.OPEN.value,
    )
    
    return complaint_dict

@router.get("/complaints", response_model=list[ComplaintResponse])
async def list_complaints(
    current_user: dict = Depends(get_current_user),
    status: ComplaintStatus | None = None,
    department: str | None = None,
    skip: int = 0,
    limit: int | None = None,
):
    """
    Role-based complaint listing:
    - CITIZEN: Only their own complaints
    - DEPT_HEAD: Complaints from their department
    - ADMIN: All complaints (with optional filtering)
    """
    db = get_database()
    query = {}
    page_size = limit if limit is not None else settings.default_page_size
    page_size = max(1, min(page_size, settings.max_page_size))
    
    user_role = current_user.get("role")
    user_id = str(current_user["_id"])
    
    # Apply role-based filters
    if user_role == UserRole.CITIZEN:
        # Citizens only see their own complaints
        query["user_id"] = user_id
    elif user_role == UserRole.DEPT_HEAD:
        # Department heads see complaints from their department
        user_dept = current_user.get("department")
        if user_dept:
            query["department"] = user_dept
        else:
            # If dept head has no department assigned, show nothing
            query["_id"] = {"$exists": False}
    elif user_role == UserRole.ADMIN:
        # Admin can filter by department if provided
        if department:
            query["department"] = department
    
    # Filter by status if provided
    if status:
        query["status"] = status.value
        
    cursor = db["complaints"].find(query).skip(skip).limit(page_size).sort("created_at", -1)
    
    complaints = []
    async for doc in cursor:
        complaints.append(fix_id(doc))
        
    return complaints

@router.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(complaint_id: str):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    db = get_database()
    doc = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    return fix_id(doc)

@router.patch("/complaints/{complaint_id}/status", response_model=ComplaintResponse)
async def update_complaint_status(
    complaint_id: str,
    status: ComplaintStatus = Body(..., embed=True),
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    db = get_database()

    existing = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or existing.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot update complaints outside your department")
    
    # Update Query
    update_data = {
        "$set": {
            "status": status, 
            "updated_at": datetime.utcnow()
        },
        "$push": {
            "status_history": {
                "status": status,
                "timestamp": datetime.utcnow(),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": "Status updated via API"
            }
        }
    }
    
    result = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        update_data,
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Notify the citizen who filed the complaint
    old_status = existing.get("status", ComplaintStatus.OPEN)
    citizen_id = existing.get("user_id")
    if citizen_id:
        status_messages = {
            ComplaintStatus.IN_PROGRESS: "Your grievance is now being reviewed by the department.",
            ComplaintStatus.RESOLVED: "Your grievance has been resolved. If the issue persists, please file a new complaint.",
            ComplaintStatus.REJECTED: "Your grievance has been reviewed and was not accepted. Please check the details.",
            ComplaintStatus.OPEN: "Your grievance has been re-opened for further review.",
        }
        dept = existing.get("department", "the department")
        msg = status_messages.get(status, f"Status updated to {status}.")
        status_val = status.value if hasattr(status, 'value') else str(status)
        old_status_val = old_status.value if hasattr(old_status, 'value') else str(old_status)
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.STATUS_CHANGE,
            title=f"Status Updated: {status_val}",
            message=f"{msg} Department: {dept}.",
            complaint_id=complaint_id,
            status_from=old_status_val,
            status_to=status_val,
        )

    return fix_id(result)


@router.post("/complaints/{complaint_id}/escalate", response_model=ComplaintResponse)
async def escalate_complaint(complaint_id: str, current_user: dict = Depends(get_current_admin_or_dept_head)):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or complaint.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot escalate complaints outside your department")

    current_authority = complaint.get("authority_id")
    authority = get_authority_by_id(current_authority) if current_authority else None
    parent_id = authority.parent_authority_id if authority else complaint.get("escalation_parent_authority_id")
    if not parent_id:
        raise HTTPException(status_code=400, detail="No escalation target available")

    update_data = {
        "$set": {
            "authority_id": parent_id,
            "updated_at": datetime.utcnow(),
        },
        "$push": {
            "status_history": {
                "status": complaint.get("status", ComplaintStatus.OPEN),
                "timestamp": datetime.utcnow(),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": f"Escalated from {current_authority} to {parent_id}",
            }
        }
    }

    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        update_data,
        return_document=True,
    )

    # Notify citizen about escalation
    citizen_id = complaint.get("user_id")
    if citizen_id:
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.ESCALATION,
            title="Grievance Escalated",
            message=f"Your grievance for {complaint.get('department', 'the department')} has been escalated to a higher authority for faster resolution.",
            complaint_id=complaint_id,
        )

    return fix_id(updated)


# ---------------------------------------------------------------------------
# Citizen feedback (star rating + comment) — only once, only after Resolved
# ---------------------------------------------------------------------------

@router.post("/complaints/{complaint_id}/feedback", response_model=ComplaintResponse)
async def submit_feedback(
    complaint_id: str,
    payload: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.get("user_id") != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your complaint")

    if complaint.get("status") != ComplaintStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Feedback can only be submitted for resolved complaints")

    if complaint.get("feedback"):
        raise HTTPException(status_code=409, detail="Feedback already submitted")

    feedback_doc = {
        "rating": payload.rating,
        "comment": payload.comment,
        "submitted_at": datetime.utcnow(),
    }
    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        {"$set": {"feedback": feedback_doc, "updated_at": datetime.utcnow()}},
        return_document=True,
    )
    return fix_id(updated)


# ---------------------------------------------------------------------------
# Internal dept notes (dept_head / admin only, hidden from citizen)
# ---------------------------------------------------------------------------

@router.post("/complaints/{complaint_id}/notes", response_model=ComplaintResponse)
async def add_dept_note(
    complaint_id: str,
    payload: DeptNoteRequest,
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or complaint.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot add notes to complaints outside your department")

    note_doc = {
        "note": payload.note,
        "created_by": current_user.get("username"),
        "created_at": datetime.utcnow(),
    }
    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"dept_notes": note_doc}, "$set": {"updated_at": datetime.utcnow()}},
        return_document=True,
    )
    return fix_id(updated)


@router.get("/complaints/{complaint_id}/notes")
async def get_dept_notes(
    complaint_id: str,
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one(
        {"_id": ObjectId(complaint_id)},
        {"dept_notes": 1},
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint.get("dept_notes", [])


# ---------------------------------------------------------------------------
# Public comments thread (visible to all parties on this complaint)
# ---------------------------------------------------------------------------

@router.post("/complaints/{complaint_id}/comments")
async def add_comment(
    complaint_id: str,
    payload: CommentRequest,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    role = current_user.get("role")
    if role == UserRole.CITIZEN and complaint.get("user_id") != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your complaint")

    comment_doc = {
        "text": payload.text,
        "author_id": str(current_user["_id"]),
        "author_name": current_user.get("username"),
        "author_role": role,
        "created_at": datetime.utcnow(),
    }
    await db["complaints"].update_one(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"comments": comment_doc}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return {"message": "Comment added", "comment": comment_doc}


@router.get("/complaints/{complaint_id}/comments")
async def get_comments(
    complaint_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    db = get_database()
    complaint = await db["complaints"].find_one(
        {"_id": ObjectId(complaint_id)},
        {"comments": 1, "user_id": 1},
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    role = current_user.get("role")
    if role == UserRole.CITIZEN and complaint.get("user_id") != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your complaint")

    return complaint.get("comments", [])


# ---------------------------------------------------------------------------
# CSV export (admin only)
# ---------------------------------------------------------------------------

@router.get("/complaints/export/csv")
async def export_complaints_csv(
    current_user: dict = Depends(get_current_admin),
    status: ComplaintStatus | None = None,
    department: str | None = None,
):
    db = get_database()
    query: dict = {}
    if status:
        query["status"] = status.value
    if department:
        query["department"] = department

    cursor = db["complaints"].find(query).sort("created_at", -1)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id", "department", "status", "priority", "description",
            "location", "created_at", "updated_at", "escalated", "user_id",
        ],
        extrasaction="ignore",
    )
    writer.writeheader()

    async for doc in cursor:
        writer.writerow({
            "id": str(doc["_id"]),
            "department": doc.get("department", ""),
            "status": doc.get("status", ""),
            "priority": doc.get("priority", ""),
            "description": doc.get("description", ""),
            "location": doc.get("location", ""),
            "created_at": doc.get("created_at", ""),
            "updated_at": doc.get("updated_at", ""),
            "escalated": doc.get("escalated", False),
            "user_id": doc.get("user_id", ""),
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=complaints_export.csv"},
    )


# ---------------------------------------------------------------------------
# Bulk operations (admin only)
# ---------------------------------------------------------------------------

@router.post("/complaints/bulk/status")
async def bulk_update_status(
    payload: BulkStatusUpdate,
    current_user: dict = Depends(get_current_admin),
):
    db = get_database()
    valid_ids = [ObjectId(cid) for cid in payload.complaint_ids if ObjectId.is_valid(cid)]
    if not valid_ids:
        raise HTTPException(status_code=400, detail="No valid complaint IDs provided")

    history_entry = {
        "status": payload.status,
        "timestamp": datetime.utcnow(),
        "changed_by_user_id": str(current_user["_id"]),
        "note": payload.note or "Bulk status update",
    }
    result = await db["complaints"].update_many(
        {"_id": {"$in": valid_ids}},
        {
            "$set": {"status": payload.status, "updated_at": datetime.utcnow()},
            "$push": {"status_history": history_entry},
        },
    )
    return {"updated": result.modified_count}


@router.post("/complaints/bulk/transfer")
async def bulk_transfer(
    payload: BulkTransfer,
    current_user: dict = Depends(get_current_admin),
):
    from app.category_utils import CANONICAL_CATEGORIES

    if payload.new_department not in CANONICAL_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid department: {payload.new_department}")

    db = get_database()
    valid_ids = [ObjectId(cid) for cid in payload.complaint_ids if ObjectId.is_valid(cid)]
    if not valid_ids:
        raise HTTPException(status_code=400, detail="No valid complaint IDs provided")

    routing = route_authority(payload.new_department)
    note = f"Bulk transferred to '{payload.new_department}'"
    if payload.reason:
        note += f". Reason: {payload.reason}"

    result = await db["complaints"].update_many(
        {"_id": {"$in": valid_ids}},
        {
            "$set": {
                "department": payload.new_department,
                "authority_id": routing.get("authority_id"),
                "routing_confidence": routing.get("confidence"),
                "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
                "updated_at": datetime.utcnow(),
            },
            "$push": {
                "status_history": {
                    "status": ComplaintStatus.OPEN,
                    "timestamp": datetime.utcnow(),
                    "changed_by_user_id": str(current_user["_id"]),
                    "note": note,
                }
            },
        },
    )
    return {"updated": result.modified_count}

@router.patch("/complaints/{complaint_id}/transfer", response_model=ComplaintResponse)
async def transfer_complaint(
    complaint_id: str,
    payload: TransferRequest,
    current_user: dict = Depends(get_current_admin_or_dept_head),
):
    """
    Transfer a grievance to a different department.
    - ADMIN: can transfer any complaint.
    - DEPT_HEAD: can only transfer complaints currently in their own department.
    The AI confidence score is irrelevant — this override is always allowed for authorised roles.
    """
    from app.category_utils import CANONICAL_CATEGORIES

    if not ObjectId.is_valid(complaint_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if payload.new_department not in CANONICAL_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department '{payload.new_department}'. Must be one of: {', '.join(CANONICAL_CATEGORIES)}",
        )

    db = get_database()
    complaint = await db["complaints"].find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Dept heads can only transfer from their own department
    if current_user.get("role") == UserRole.DEPT_HEAD:
        user_dept = current_user.get("department")
        if not user_dept or complaint.get("department") != user_dept:
            raise HTTPException(status_code=403, detail="Cannot transfer complaints outside your department")

    old_dept = complaint.get("department", "Unknown")
    new_dept = payload.new_department

    if old_dept == new_dept:
        raise HTTPException(status_code=400, detail="Complaint is already assigned to this department")

    # Re-derive authority routing for the new department
    routing = route_authority(new_dept)

    transfer_note = f"Transferred from '{old_dept}' to '{new_dept}'"
    if payload.reason:
        transfer_note += f". Reason: {payload.reason}"

    update_data = {
        "$set": {
            "department": new_dept,
            "authority_id": routing.get("authority_id"),
            "routing_confidence": routing.get("confidence"),
            "escalation_parent_authority_id": routing.get("escalation_parent_authority_id"),
            "updated_at": datetime.utcnow(),
        },
        "$push": {
            "status_history": {
                "status": complaint.get("status", ComplaintStatus.OPEN),
                "timestamp": datetime.utcnow(),
                "changed_by_user_id": str(current_user.get("_id")),
                "note": transfer_note,
            }
        },
    }

    updated = await db["complaints"].find_one_and_update(
        {"_id": ObjectId(complaint_id)},
        update_data,
        return_document=True,
    )

    # Notify the citizen
    citizen_id = complaint.get("user_id")
    if citizen_id:
        citizen_msg = (
            f"Your grievance has been transferred from {old_dept} to {new_dept}."
        )
        if payload.reason:
            citizen_msg += f" Reason: {payload.reason}"
        await create_notification(
            user_id=citizen_id,
            notification_type=NotificationType.ASSIGNMENT,
            title="Grievance Transferred to New Department",
            message=citizen_msg,
            complaint_id=complaint_id,
        )

    return fix_id(updated)
