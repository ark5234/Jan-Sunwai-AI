"""
Auto-assignment service for Jan-Sunwai AI.

Assignment algorithm:
1. Find approved workers in the complaint's department whose service area
   covers the complaint's location (haversine distance check).
2. Sort eligible workers by active task count (least-loaded first).
3. Assign to the best worker: push complaint into active_complaint_ids,
   set worker status to busy.
4. If no eligible worker → complaint stays Open / Unassigned.

When a worker marks a task done, free_worker_slot() removes the complaint
from the worker's active list and, if now empty, resets status to available.
It then re-queues any nearby Open+Unassigned complaints in that area.
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from app.schemas import ComplaintStatus

logger = logging.getLogger("JanSunwaiAI.assignment")


# ---------------------------------------------------------------------------
# Haversine distance helper
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two points."""
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Core assign / free helpers
# ---------------------------------------------------------------------------

MAX_ACTIVE_TASKS = 5  # hard cap per worker


async def _do_assign(db, worker: dict, complaint_id: str) -> None:
    """Atomically assign a complaint to a worker, enforcing MAX_ACTIVE_TASKS.

    Uses a conditional filter on the worker update so the write is a no-op
    if the worker already has MAX_ACTIVE_TASKS — preventing race conditions
    where two concurrent requests both read the same worker as 'available'.
    """
    worker_id = str(worker["_id"])
    now = datetime.now(timezone.utc)

    # Atomic conditional: only proceed if active_complaint_ids size < MAX_ACTIVE_TASKS
    result = await db["users"].update_one(
        {
            "_id": ObjectId(worker_id),
            f"active_complaint_ids.{MAX_ACTIVE_TASKS - 1}": {"$exists": False},  # array length < MAX
        },
        {
            "$addToSet": {"active_complaint_ids": complaint_id},
            "$set": {
                "worker_status": "busy",
                "updated_at": now,
            },
        },
    )

    if result.matched_count == 0:
        logger.warning(
            "Assignment skipped: worker %s (%s) already at MAX_ACTIVE_TASKS=%d or no longer exists",
            worker.get("username"),
            worker_id,
            MAX_ACTIVE_TASKS,
        )
        return

    await db["complaints"].update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "assigned_to": worker_id,
                "status": ComplaintStatus.IN_PROGRESS,
                "updated_at": now,
            },
            "$push": {
                "status_history": {
                    "status": ComplaintStatus.IN_PROGRESS,
                    "timestamp": now,
                    "changed_by_user_id": "system",
                    "note": f"Auto-assigned to field worker {worker.get('username', worker_id)}",
                }
            },
        },
    )
    logger.info(
        "Complaint %s assigned to worker %s (%s) → status: %s",
        complaint_id,
        worker.get("username"),
        worker_id,
        ComplaintStatus.IN_PROGRESS,
    )


async def auto_assign(
    complaint_id: str,
    department: str,
    complaint_location: Optional[dict],
    db,
) -> Optional[str]:
    """
    Find the best available worker for a complaint and assign it.

    Returns the assigned worker_id, or None if no eligible worker found.
    complaint_location: {"lat": float, "lon": float} or None
    """
    # Build query for eligible workers
    query: dict = {
        "role": "worker",
        "is_approved": True,
        "department": department,
        "worker_status": {"$ne": "offline"},
    }

    # Fetch all candidate workers (small collections — fine to load all)
    candidates = []
    async for worker in db["users"].find(query):
        # If complaint has geo location, apply area filter
        if complaint_location:
            c_lat = complaint_location.get("lat")
            c_lon = complaint_location.get("lon")
            sa = worker.get("service_area")
            if sa and c_lat is not None and c_lon is not None:
                dist = _haversine_km(sa["lat"], sa["lon"], c_lat, c_lon)
                if dist > sa.get("radius_km", 5.0):
                    continue  # outside this worker's service area
        candidates.append(worker)

    if not candidates:
        logger.info(
            "No eligible worker for complaint %s in dept '%s'",
            complaint_id,
            department,
        )
        return None

    # Sort by fewest active complaints (load balancing)
    candidates.sort(key=lambda w: len(w.get("active_complaint_ids", [])))
    best = candidates[0]

    await _do_assign(db, best, complaint_id)
    return str(best["_id"])


async def free_worker_slot(worker_id: str, complaint_id: str, db) -> None:
    """
    Remove a complaint from the worker's active list.
    If the list becomes empty, restore worker status to 'available'.
    Then try to assign at most ONE unassigned Open complaint in the worker's area
    to avoid overwhelming the worker immediately after freeing.
    """
    now = datetime.now(timezone.utc)
    worker = await db["users"].find_one({"_id": ObjectId(worker_id)})
    if not worker:
        logger.warning("free_worker_slot: worker %s not found", worker_id)
        return

    active = [c for c in worker.get("active_complaint_ids", []) if c != complaint_id]
    new_status = "available" if not active else "busy"

    await db["users"].update_one(
        {"_id": ObjectId(worker_id)},
        {
            "$set": {
                "active_complaint_ids": active,
                "worker_status": new_status,
                "updated_at": now,
            }
        },
    )
    logger.info(
        "Worker %s freed from complaint %s → status: %s  active_tasks: %d",
        worker_id,
        complaint_id,
        new_status,
        len(active),
    )

    # Reassign at most ONE pending complaint to avoid overwhelming the worker.
    if new_status == "available":
        department = worker.get("department")
        sa = worker.get("service_area")

        if not department:
            return

        unassigned_cursor = db["complaints"].find(
            {
                "department": department,
                "status": ComplaintStatus.OPEN,
                "$or": [{"assigned_to": None}, {"assigned_to": {"$exists": False}}],
            }
        ).sort("created_at", 1).limit(10)  # fetch a few to allow area filtering

        async for complaint in unassigned_cursor:
            cid = str(complaint["_id"])
            loc = complaint.get("location")
            # Check area overlap
            if sa and loc:
                c_lat = loc.get("lat")
                c_lon = loc.get("lon")
                if c_lat is not None and c_lon is not None:
                    dist = _haversine_km(sa["lat"], sa["lon"], c_lat, c_lon)
                    if dist > sa.get("radius_km", 5.0):
                        continue
            # Assign the first matching complaint and stop
            await _do_assign(db, worker, cid)
            logger.info(
                "Re-assigned complaint %s to freed worker %s (%s)",
                cid,
                worker.get("username"),
                worker_id,
            )
            break  # at most ONE reassignment
