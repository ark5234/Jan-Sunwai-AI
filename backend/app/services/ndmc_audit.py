import logging
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.database import get_ndmc_database


logger = logging.getLogger("JanSunwaiAI.ndmc.audit")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


async def record_ndmc_analysis(
    *,
    complaint_id: str,
    user_id: str,
    image_url: str,
    analysis_token: str | None,
    local_result: dict[str, Any],
    ndmc_result: dict[str, Any],
    comparison: dict[str, Any] | None,
    explainability: dict[str, Any] | None,
    final_department: str,
    final_confidence: float | int | None,
    user_text_result: dict[str, Any] | None = None,
) -> bool:
    try:
        database = get_ndmc_database()
    except RuntimeError as exc:
        logger.warning("Skipping NDMC audit write: %s", exc)
        return False

    now = datetime.now(timezone.utc)
    comparison_doc = _as_dict(comparison)
    explain_doc = _as_dict(explainability)

    document = {
        "complaint_id": str(complaint_id),
        "user_id": str(user_id),
        "image_url": image_url,
        "analysis_token": analysis_token,
        "local_category": local_result.get("category"),
        "local_confidence": local_result.get("confidence"),
        "ndmc_category": ndmc_result.get("category"),
        "ndmc_confidence": ndmc_result.get("confidence"),
        "ndmc_server_version": ndmc_result.get("server_version"),
        "ndmc_http_status": ndmc_result.get("http_status"),
        "ndmc_response_headers": ndmc_result.get("response_headers") or {},
        "ndmc_candidates": ndmc_result.get("candidates") or [],
        "ndmc_raw_response": ndmc_result.get("raw_response") or {},
        "local_candidates": explain_doc.get("local_candidates") or [],
        "selected_method": comparison_doc.get("method"),
        "selected_department": final_department,
        "selected_confidence": final_confidence,
        "decision_reason": _as_dict(comparison_doc.get("comparison")).get("reason"),
        "comparison": comparison_doc,
        "explainability": explain_doc,
        "user_text_result": user_text_result or {},
        "analysis_source": "api",
        "analysis_version": 1,
        "created_at": now,
        "updated_at": now,
    }

    if document["selected_method"] is None:
        document["selected_method"] = "unknown"

    await database[settings.ndmc_analysis_collection].insert_one(document)
    return True