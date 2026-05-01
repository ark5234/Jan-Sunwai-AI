"""Export the dedicated NDMC Mongo audit collection to CSV."""

from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

from dotenv import load_dotenv


FIELDNAMES = [
    "complaint_id",
    "user_id",
    "image_url",
    "ndmc_server_version",
    "selected_method",
    "selected_department",
    "selected_confidence",
    "local_category",
    "local_confidence",
    "ndmc_category",
    "ndmc_confidence",
    "decision_reason",
    "created_at",
    "updated_at",
]


def _load_env() -> None:
    load_dotenv(Path(__file__).resolve().parent / ".env")


async def _run(output_path: Path, ndmc_server_version: str | None = None, selected_method: str | None = None) -> None:
    from app.config import settings
    from app.database import connect_to_mongo, close_mongo_connection, get_ndmc_database

    await connect_to_mongo()
    ndmc_db = get_ndmc_database()

    query: dict = {}
    if ndmc_server_version:
        query["ndmc_server_version"] = ndmc_server_version
    if selected_method:
        query["selected_method"] = selected_method

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()

        async for doc in ndmc_db[settings.ndmc_analysis_collection].find(query).sort("created_at", -1):
            writer.writerow({
                "complaint_id": doc.get("complaint_id", ""),
                "user_id": doc.get("user_id", ""),
                "image_url": doc.get("image_url", ""),
                "ndmc_server_version": doc.get("ndmc_server_version", ""),
                "selected_method": doc.get("selected_method", ""),
                "selected_department": doc.get("selected_department", ""),
                "selected_confidence": doc.get("selected_confidence", ""),
                "local_category": doc.get("local_category", ""),
                "local_confidence": doc.get("local_confidence", ""),
                "ndmc_category": doc.get("ndmc_category", ""),
                "ndmc_confidence": doc.get("ndmc_confidence", ""),
                "decision_reason": doc.get("decision_reason", ""),
                "created_at": doc.get("created_at", ""),
                "updated_at": doc.get("updated_at", ""),
            })

    print(f"Exported NDMC analysis CSV to {output_path}")
    await close_mongo_connection()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export NDMC audit records to CSV")
    parser.add_argument("--output", default="triage_output/ndmc_analysis_export.csv", help="CSV output file path")
    parser.add_argument("--ndmc-server-version", default=None, help="Only export records for a specific NDMC server version")
    parser.add_argument("--selected-method", default=None, help="Only export records for a specific selected method")
    args = parser.parse_args()

    _load_env()
    asyncio.run(_run(Path(args.output), args.ndmc_server_version, args.selected_method))


if __name__ == "__main__":
    main()