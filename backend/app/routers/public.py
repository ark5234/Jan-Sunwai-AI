"""
Public transparency board — no authentication required.
Returns anonymised complaint data (no user ID, description, or image URL).
"""
from fastapi import APIRouter

from app.database import get_database

router = APIRouter(prefix="/public", tags=["Public"])


@router.get("/complaints")
async def public_complaints():
    """
    Return up to 200 recent complaints with anonymised content.
    Suitable for a public-facing transparency dashboard.
    """
    db = get_database()
    cursor = (
        db["complaints"]
        .find(
            {"status": {"$in": ["Open", "In Progress", "Resolved", "Rejected"]}},
            {
                "_id": 1,
                "department": 1,
                "status": 1,
                "location": 1,
                "created_at": 1,
                "updated_at": 1,
                "priority": 1,
                # deliberately excluded: user_id, description, image_url, ai_metadata
            },
        )
        .sort("created_at", -1)
        .limit(200)
    )
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results
