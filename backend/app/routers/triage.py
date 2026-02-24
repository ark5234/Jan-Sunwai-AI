from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
except Exception:
    pd = None
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_admin


router = APIRouter(prefix="/triage", tags=["Triage"])

TRIAGE_ROOT = Path("triage_output")
REVIEW_QUEUE_CSV = TRIAGE_ROOT / "review_queue.csv"
REVIEW_DECISIONS_CSV = TRIAGE_ROOT / "review_decisions.csv"


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
    _require_pandas()
    if not REVIEW_QUEUE_CSV.exists():
        return {"items": [], "total": 0}

    df = pd.read_csv(REVIEW_QUEUE_CSV)
    total = len(df)
    rows = df.iloc[skip : skip + limit].fillna("").to_dict(orient="records")
    return {"items": rows, "total": total}


@router.post("/review-queue/decision")
async def submit_review_decision(payload: ReviewDecision, current_user: dict = Depends(get_current_admin)):
    _require_pandas()
    TRIAGE_ROOT.mkdir(parents=True, exist_ok=True)

    row = {
        "image": payload.image,
        "decision": payload.decision,
        "corrected_label": payload.corrected_label,
        "note": payload.note,
        "reviewed_by": current_user.get("username"),
        "reviewed_at": datetime.utcnow().isoformat(),
    }

    if REVIEW_DECISIONS_CSV.exists():
        existing = pd.read_csv(REVIEW_DECISIONS_CSV)
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        updated.to_csv(REVIEW_DECISIONS_CSV, index=False)
    else:
        pd.DataFrame([row]).to_csv(REVIEW_DECISIONS_CSV, index=False)

    return {"message": "Decision saved"}
