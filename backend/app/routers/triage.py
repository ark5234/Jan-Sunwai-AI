from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
except Exception:
    pd = None
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_admin
from app.database import get_database
from app.schemas import ComplaintStatus


router = APIRouter(prefix="/triage", tags=["Triage"])

TRIAGE_ROOT = Path("triage_output")
REVIEW_QUEUE_CSV = TRIAGE_ROOT / "review_queue.csv"
REVIEW_DECISIONS_CSV = TRIAGE_ROOT / "review_decisions.csv"

CONFIDENCE_THRESHOLD = 0.65  # complaints below this appear in the review queue


class ReviewDecision(BaseModel):
    image: str
    decision: str
    corrected_label: Optional[str] = None
    note: Optional[str] = None


def _require_pandas():
    if pd is None:
        raise HTTPException(
            status_code=503,
            detail="Triage service dependency missing: pandas is not installed on backend runtime",
        )


@router.get("/review-queue")
async def get_review_queue(skip: int = 0, limit: int = 50, _: dict = Depends(get_current_admin)):
    """Return complaints whose AI confidence is below the threshold,
    queried live from MongoDB so newly submitted complaints appear immediately."""
    db = get_database()
    query = {
        "ai_metadata.confidence_score": {"$lt": CONFIDENCE_THRESHOLD},
        "status": {"$nin": [ComplaintStatus.REJECTED.value]},
        "triage_decision": {"$exists": False},  # hide already-reviewed ones
    }
    total = await db["complaints"].count_documents(query)
    cursor = db["complaints"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for doc in docs:
        ai = doc.get("ai_metadata") or {}
        loc = doc.get("location") or {}
        items.append({
            "id": str(doc["_id"]),
            "image": doc.get("image_url", ""),
            "final_label": doc.get("department", "—"),
            "confidence": ai.get("confidence_score"),
            "rationale": doc.get("description", ""),
            "model_used": ai.get("model_used", ""),
            "location": loc.get("address", ""),
            "created_at": doc.get("created_at", "").isoformat() if doc.get("created_at") else "",
        })

    return {"items": items, "total": total}


@router.post("/review-queue/decision")
async def submit_review_decision(payload: ReviewDecision, current_user: dict = Depends(get_current_admin)):
    """Record a triage decision and stamp the complaint so it leaves the queue."""
    db = get_database()
    from bson import ObjectId

    update = {
        "triage_decision": payload.decision,
        "triage_reviewed_by": current_user.get("username"),
        "triage_reviewed_at": datetime.now(timezone.utc),
    }
    if payload.corrected_label:
        update["department"] = payload.corrected_label

    filters = [{"image_url": payload.image}]
    if ObjectId.is_valid(payload.image):
        filters.insert(0, {"_id": ObjectId(payload.image)})

    updated_any = False
    for flt in filters:
        result = await db["complaints"].update_one(flt, {"$set": update})
        if result.matched_count > 0:
            updated_any = True
            break

    if not updated_any:
        raise HTTPException(status_code=404, detail="Complaint not found for supplied image/id")

    # Also persist to CSV for audit trail
    if pd is not None:
        TRIAGE_ROOT.mkdir(parents=True, exist_ok=True)
        row = {
            "image": payload.image,
            "decision": payload.decision,
            "corrected_label": payload.corrected_label,
            "note": payload.note,
            "reviewed_by": current_user.get("username"),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        if REVIEW_DECISIONS_CSV.exists():
            existing = pd.read_csv(REVIEW_DECISIONS_CSV)
            pd.concat([existing, pd.DataFrame([row])], ignore_index=True).to_csv(REVIEW_DECISIONS_CSV, index=False)
        else:
            pd.DataFrame([row]).to_csv(REVIEW_DECISIONS_CSV, index=False)

    return {"message": "Decision saved", "updated": True}
