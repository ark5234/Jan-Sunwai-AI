"""
Public transparency board — no authentication required.
Returns anonymised complaint data (no user ID, description, or image URL).
"""
from fastapi import APIRouter

from app.database import get_database
from app.schemas import ComplaintStatus

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
            {
                "status": {
                    "$in": [
                        ComplaintStatus.OPEN.value,
                        ComplaintStatus.IN_PROGRESS.value,
                        ComplaintStatus.RESOLVED.value,
                        ComplaintStatus.REJECTED.value,
                    ]
                }
            },
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
        loc = doc.get("location") or {}
        try:
            lat = float(loc.get("lat"))
            lon = float(loc.get("lon"))
            coarse_location = {
                "lat": round(lat, 2),
                "lon": round(lon, 2),
                "source": loc.get("source"),
            }
        except (TypeError, ValueError):
            coarse_location = {"source": loc.get("source")}

        doc["_id"] = str(doc["_id"])
        doc["location"] = coarse_location
        results.append(doc)
    return results
