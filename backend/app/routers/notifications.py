from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Body

from app.auth import get_current_user
from app.database import get_database
from app.schemas import NotificationResponse, NotificationType

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def fix_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ---------------------------------------------------------------------------
# Helper: create a notification (called from other routers)
# ---------------------------------------------------------------------------

async def create_notification(
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    complaint_id: str | None = None,
    status_from: str | None = None,
    status_to: str | None = None,
):
    """Insert a notification document into MongoDB."""
    db = get_database()
    doc = {
        "user_id": user_id,
        "complaint_id": complaint_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "status_from": status_from,
        "status_to": status_to,
        "is_read": False,
        "created_at": datetime.utcnow(),
    }
    await db["notifications"].insert_one(doc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 30,
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Return notifications for the logged-in user, newest first."""
    db = get_database()
    query: dict = {"user_id": str(current_user["_id"])}
    if unread_only:
        query["is_read"] = False

    cursor = (
        db["notifications"]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(max(1, min(limit, 100)))
    )

    results = []
    async for doc in cursor:
        results.append(fix_id(doc))
    return results


@router.get("/unread-count")
async def unread_count(current_user: dict = Depends(get_current_user)):
    """Return the number of unread notifications for the badge."""
    db = get_database()
    count = await db["notifications"].count_documents(
        {"user_id": str(current_user["_id"]), "is_read": False}
    )
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="Invalid notification ID")

    db = get_database()
    result = await db["notifications"].update_one(
        {"_id": ObjectId(notification_id), "user_id": str(current_user["_id"])},
        {"$set": {"is_read": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


@router.patch("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db["notifications"].update_many(
        {"user_id": str(current_user["_id"]), "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"status": "ok"}
