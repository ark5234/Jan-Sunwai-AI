"""Backfill the dedicated NDMC Mongo database from existing complaint records.

This replays the NDMC call for complaints that have an image URL and stores a
new audit document in the NDMC database.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    load_dotenv(Path(__file__).resolve().parent / ".env")


async def _run(limit: int | None = None, skip_existing: bool = True) -> None:
    from app.config import settings
    from app.database import connect_to_mongo, close_mongo_connection, get_database, get_ndmc_database
    from app.ndmc_api_client import call_ndmc_api, compare_classifications
    from app.services.ndmc_audit import record_ndmc_analysis
    from app.services.storage import storage_service

    await connect_to_mongo()
    main_db = get_database()
    ndmc_db = get_ndmc_database()

    existing_ids: set[str] = set()
    if skip_existing:
        async for doc in ndmc_db[settings.ndmc_analysis_collection].find({}, {"complaint_id": 1}):
            if doc.get("complaint_id"):
                existing_ids.add(str(doc["complaint_id"]))

    query: dict = {"image_url": {"$exists": True, "$ne": ""}}
    cursor = main_db["complaints"].find(query).sort("created_at", -1)
    if limit is not None:
        cursor = cursor.limit(limit)

    processed = 0
    async for complaint in cursor:
        complaint_id = str(complaint["_id"])
        if skip_existing and complaint_id in existing_ids:
            continue

        image_path = storage_service.resolve_path(str(complaint.get("image_url", "")))
        ndmc_result = await asyncio.to_thread(call_ndmc_api, image_path)
        local_result = {
            "category": complaint.get("department", "Uncategorized"),
            "confidence": (complaint.get("ai_metadata") or {}).get("confidence_score", 0.0),
        }
        comparison = compare_classifications(local_result, ndmc_result)
        explainability = (complaint.get("ai_metadata") or {}).get("explainability") or {}

        await record_ndmc_analysis(
            complaint_id=complaint_id,
            user_id=str(complaint.get("user_id", "")),
            image_url=str(complaint.get("image_url", "")),
            analysis_token=None,
            local_result=local_result,
            ndmc_result=ndmc_result,
            comparison=comparison,
            explainability=explainability,
            final_department=str(comparison.get("category") or complaint.get("department") or "Uncategorized"),
            final_confidence=comparison.get("confidence", 0.0),
            user_text_result=None,
        )
        processed += 1
        print(f"Backfilled NDMC audit for complaint {complaint_id}")

    print(f"Backfill complete. Processed {processed} complaint(s).")
    await close_mongo_connection()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill NDMC audit records into the NDMC Mongo database")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of complaints to process")
    parser.add_argument("--no-skip-existing", action="store_true", help="Reprocess complaints already in the NDMC DB")
    args = parser.parse_args()

    _load_env()
    asyncio.run(_run(limit=args.limit, skip_existing=not args.no_skip_existing))


if __name__ == "__main__":
    main()