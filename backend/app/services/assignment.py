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
from datetime import datetime
from typing import Optional
from bson import ObjectId

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

async def _do_assign(db, worker: dict, complaint_id: str) -> None:
    """Atomically push a complaint onto a worker's active list, set worker busy,
    and advance the complaint status to In Progress."""
    worker_id = str(worker["_id"])
    await db["users"].update_one(
        {"_id": ObjectId(worker_id)},
        {
            "$addToSet": {"active_complaint_ids": complaint_id},
            "$set": {
                "worker_status": "busy",
                "updated_at": datetime.utcnow(),
            },
        },
    )
    await db["complaints"].update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "assigned_to": worker_id,
                "status": "In Progress",
                "updated_at": datetime.utcnow(),
            },
            "$push": {
                "status_history": {
                    "status": "In Progress",
                    "timestamp": datetime.utcnow(),
                    "changed_by_user_id": worker_id,
                    "note": f"Auto-assigned to field worker {worker.get('username', worker_id)}",
                }
            },
        },
    )
    logger.info(
        "Complaint %s assigned to worker %s (%s) → status set to In Progress",
        complaint_id,
        worker.get("username"),
        worker_id,
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
    Then try to assign any unassigned Open complaints in the worker's area.
    """
    worker = await db["users"].find_one({"_id": ObjectId(worker_id)})
    if not worker:
        return

    active = [c for c in worker.get("active_complaint_ids", []) if c != complaint_id]
    new_status = "available" if not active else "busy"

    await db["users"].update_one(
        {"_id": ObjectId(worker_id)},
        {
            "$set": {
                "active_complaint_ids": active,
                "worker_status": new_status,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    logger.info(
        "Worker %s freed from complaint %s. Status → %s. Active tasks: %d",
        worker_id,
        complaint_id,
        new_status,
        len(active),
    )

    # -----------------------------------------------------------------------
    # Re-run assignment for any Open+Unassigned complaints in the worker's
    # department that overlap with this worker's service area.
    # -----------------------------------------------------------------------
    if new_status == "available":
        department = worker.get("department")
        sa = worker.get("service_area")

        if not department:
            return

        # Find up to 5 unassigned Open complaints in the same department
        unassigned_cursor = db["complaints"].find(
            {
                "department": department,
                "status": "Open",
                "$or": [{"assigned_to": None}, {"assigned_to": {"$exists": False}}],
            }
        ).sort("created_at", 1).limit(5)

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
            await _do_assign(db, worker, cid)
            logger.info("Re-assigned queued complaint %s to freed worker %s", cid, worker_id)
