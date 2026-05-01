from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.chdir(BACKEND_DIR)
load_dotenv(BACKEND_DIR / ".env")

from app.category_utils import canonicalize_label
from app.ndmc_api_client import call_ndmc_api, compare_classifications
from app.services.storage import storage_service


DEFAULT_OUTPUT = BACKEND_DIR / "triage_output" / "ndmc_mongo_agreement_report.csv"
DEFAULT_SUMMARY = BACKEND_DIR / "triage_output" / "ndmc_mongo_agreement_summary.csv"


def _load_mongo_client() -> MongoClient:
    mongo_url = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    return MongoClient(mongo_url)


def _normalize_image_url(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _resolve_image_path(image_url: str) -> Path | None:
    if not image_url:
        return None
    try:
        return Path(storage_service.resolve_path(image_url))
    except Exception:
        return None


def _sample_docs(docs: list[dict[str, Any]], sample_size: int, seed: int) -> list[dict[str, Any]]:
    if sample_size <= 0 or sample_size >= len(docs):
        return docs
    rng = random.Random(seed)
    return rng.sample(docs, sample_size)


def _pick_stored_label(doc: dict[str, Any]) -> str:
    department = str(doc.get("department") or "").strip()
    if department:
        return department

    ai_metadata = doc.get("ai_metadata") or {}
    if isinstance(ai_metadata, dict):
        return str(ai_metadata.get("detected_department") or ai_metadata.get("department") or "Uncategorized")

    return "Uncategorized"


def _pick_stored_confidence(doc: dict[str, Any]) -> float:
    ai_metadata = doc.get("ai_metadata") or {}
    if isinstance(ai_metadata, dict):
        try:
            return float(ai_metadata.get("confidence_score") or ai_metadata.get("confidence") or 0.0)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _make_report_row(doc: dict[str, Any], image_path: Path, ndmc_result: dict[str, Any]) -> dict[str, Any]:
    stored_department = _pick_stored_label(doc)
    stored_confidence = _pick_stored_confidence(doc)
    stored_ai_department = "Uncategorized"
    ai_metadata = doc.get("ai_metadata") or {}
    if isinstance(ai_metadata, dict):
        stored_ai_department = str(ai_metadata.get("detected_department") or ai_metadata.get("department") or "Uncategorized")

    local_result = {"category": stored_department, "confidence": stored_confidence}
    comparison = compare_classifications(local_result, ndmc_result)
    agreement = bool(comparison.get("comparison", {}).get("match", False))

    ndmc_label = str(ndmc_result.get("category", "Uncategorized"))
    ndmc_confidence = float(ndmc_result.get("confidence", 0.0) or 0.0)

    return {
        "complaint_id": str(doc.get("_id", "")),
        "image_url": _normalize_image_url(doc.get("image_url", "")),
        "resolved_image_path": str(image_path) if image_path else "",
        "stored_department": stored_department,
        "stored_department_canonical": canonicalize_label(stored_department),
        "stored_ai_department": stored_ai_department,
        "stored_ai_department_canonical": canonicalize_label(stored_ai_department),
        "stored_confidence": f"{stored_confidence:.4f}",
        "ndmc_department": ndmc_label,
        "ndmc_department_canonical": canonicalize_label(ndmc_label),
        "ndmc_confidence": f"{ndmc_confidence:.4f}",
        "ndmc_success": str(bool(ndmc_result.get("success", False))),
        "selected_department": comparison["category"],
        "selected_method": comparison["method"],
        "agreement": str(agreement),
        "comparison_reason": comparison.get("comparison", {}).get("reason", ""),
        "ndmc_error": ndmc_result.get("error", "") or "",
        "created_at": doc.get("created_at", ""),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_report(sample_size: int, seed: int, output: Path, summary_output: Path, collection_name: str) -> None:
    client = _load_mongo_client()
    mongo_url = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
    db_name = os.getenv("DB_NAME", "jan_sunwai_db")
    db = client[db_name]
    collection = db[collection_name]

    query = {
        "image_url": {"$exists": True, "$ne": ""},
    }
    docs = list(collection.find(query, sort=[("created_at", -1)]))
    if not docs:
        raise RuntimeError(f"No complaint documents with image_url found in {db_name}.{collection_name}")

    sampled_docs = _sample_docs(docs, sample_size, seed)

    report_rows: list[dict[str, Any]] = []
    confusion_counter: Counter[tuple[str, str]] = Counter()
    ndmc_successes = 0
    agreements = 0
    skipped_missing_images = 0

    for doc in sampled_docs:
        image_url = _normalize_image_url(doc.get("image_url", ""))
        image_path = _resolve_image_path(image_url)
        if image_path is None or not image_path.exists():
            skipped_missing_images += 1
            report_rows.append(
                {
                    "complaint_id": str(doc.get("_id", "")),
                    "image_url": image_url,
                    "resolved_image_path": str(image_path) if image_path else "",
                    "stored_department": _pick_stored_label(doc),
                    "stored_department_canonical": canonicalize_label(_pick_stored_label(doc)),
                    "stored_ai_department": str((doc.get("ai_metadata") or {}).get("detected_department") or "Uncategorized"),
                    "stored_ai_department_canonical": canonicalize_label(str((doc.get("ai_metadata") or {}).get("detected_department") or "Uncategorized")),
                    "stored_confidence": f"{_pick_stored_confidence(doc):.4f}",
                    "ndmc_department": "Uncategorized",
                    "ndmc_department_canonical": "Uncategorized",
                    "ndmc_confidence": "0.0000",
                    "ndmc_success": "False",
                    "selected_department": _pick_stored_label(doc),
                    "selected_method": "local_by_default",
                    "agreement": "False",
                    "comparison_reason": "Image missing on disk",
                    "ndmc_error": "image missing on disk",
                    "created_at": doc.get("created_at", ""),
                }
            )
            continue

        ndmc_result = call_ndmc_api(str(image_path))
        report_row = _make_report_row(doc, image_path, ndmc_result)
        report_rows.append(report_row)

        if ndmc_result.get("success", False):
            ndmc_successes += 1
            if report_row["agreement"] == "True":
                agreements += 1
            else:
                confusion_counter[(report_row["stored_department_canonical"], report_row["ndmc_department_canonical"])] += 1

    report_fields = [
        "complaint_id",
        "image_url",
        "resolved_image_path",
        "stored_department",
        "stored_department_canonical",
        "stored_ai_department",
        "stored_ai_department_canonical",
        "stored_confidence",
        "ndmc_department",
        "ndmc_department_canonical",
        "ndmc_confidence",
        "ndmc_success",
        "selected_department",
        "selected_method",
        "agreement",
        "comparison_reason",
        "ndmc_error",
        "created_at",
    ]
    _write_csv(output, report_rows, report_fields)

    agreement_rate = agreements / ndmc_successes if ndmc_successes else 0.0
    top_confusions = confusion_counter.most_common(5)

    summary_rows: list[dict[str, Any]] = [
        {"metric": "sample_size", "value": len(report_rows), "details": "sampled complaints from MongoDB"},
        {"metric": "missing_images", "value": skipped_missing_images, "details": "documents skipped due to missing uploaded files"},
        {"metric": "ndmc_successes", "value": ndmc_successes, "details": "successful NDMC responses"},
        {"metric": "agreement_rate", "value": f"{agreement_rate:.4f}", "details": f"{agreements}/{ndmc_successes or 0}"},
    ]
    for index, ((stored_label, ndmc_label), count) in enumerate(top_confusions, start=1):
        summary_rows.append(
            {
                "metric": f"top_confusion_{index}",
                "value": count,
                "details": f"{stored_label} -> {ndmc_label}",
            }
        )
    if not top_confusions:
        summary_rows.append({"metric": "top_confusion_1", "value": 0, "details": "no mismatches in successful NDMC comparisons"})

    _write_csv(summary_output, summary_rows, ["metric", "value", "details"])

    print(f"MongoDB source: {mongo_url} / {db_name}.{collection_name}")
    print(f"Sampled complaints: {len(report_rows)}")
    print(f"Missing images: {skipped_missing_images}")
    print(f"NDMC successes: {ndmc_successes}")
    print(f"Agreement rate: {agreement_rate:.1%}")
    if top_confusions:
        print("Top confusions:")
        for index, ((stored_label, ndmc_label), count) in enumerate(top_confusions, start=1):
            print(f"  {index}. {stored_label} -> {ndmc_label}: {count}")
    print(f"Report CSV: {output}")
    print(f"Summary CSV: {summary_output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NDMC agreement analysis against complaints stored in MongoDB.")
    parser.add_argument("--sample", type=int, default=20, help="Number of MongoDB complaints to sample.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write the per-case CSV report.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=DEFAULT_SUMMARY,
        help="Where to write the summary CSV report.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="complaints",
        help="MongoDB collection to read complaints from.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_report(
        sample_size=args.sample,
        seed=args.seed,
        output=args.output,
        summary_output=args.summary_output,
        collection_name=args.collection,
    )