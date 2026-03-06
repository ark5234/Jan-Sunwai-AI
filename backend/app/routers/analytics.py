"""
Analytics endpoints — admin only.
Provides aggregated statistics for the admin dashboard.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from app.auth import get_current_admin
from app.database import get_database

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def analytics_overview(current_user: dict = Depends(get_current_admin)):
    db = get_database()

    # --- status breakdown ---
    status_cursor = db["complaints"].aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])
    by_status: dict = {}
    async for doc in status_cursor:
        if doc["_id"]:
            by_status[doc["_id"]] = doc["count"]

    # --- by department ---
    dept_cursor = db["complaints"].aggregate([
        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ])
    by_department = []
    async for doc in dept_cursor:
        if doc["_id"]:
            by_department.append({"department": doc["_id"], "count": doc["count"]})

    # --- monthly trend (last 6 months) ---
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_cursor = db["complaints"].aggregate([
        {"$match": {"created_at": {"$gte": six_months_ago}}},
        {"$group": {
            "_id": {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
    ])
    monthly_trend = []
    async for doc in monthly_cursor:
        monthly_trend.append({
            "year": doc["_id"]["year"],
            "month": doc["_id"]["month"],
            "count": doc["count"],
        })

    # --- average resolution time by dept (in days) ---
    resolution_cursor = db["complaints"].aggregate([
        {"$match": {"status": "Resolved", "updated_at": {"$exists": True}}},
        {"$project": {
            "department": 1,
            "resolution_days": {
                "$divide": [
                    {"$subtract": ["$updated_at", "$created_at"]},
                    86400000,  # ms → days
                ]
            },
        }},
        {"$group": {
            "_id": "$department",
            "avg_days": {"$avg": "$resolution_days"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"avg_days": 1}},
    ])
    resolution_time = []
    async for doc in resolution_cursor:
        if doc["_id"]:
            resolution_time.append({
                "department": doc["_id"],
                "avg_days": round(doc["avg_days"], 1),
                "count": doc["count"],
            })

    # --- priority breakdown ---
    priority_cursor = db["complaints"].aggregate([
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ])
    by_priority: dict = {}
    async for doc in priority_cursor:
        if doc["_id"]:
            by_priority[doc["_id"]] = doc["count"]

    # --- summary stats ---
    total = sum(by_status.values())
    resolved = by_status.get("Resolved", 0)

    return {
        "total_complaints": total,
        "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
        "by_status": by_status,
        "by_department": by_department,
        "monthly_trend": monthly_trend,
        "resolution_time_by_dept": resolution_time,
        "by_priority": by_priority,
    }
