from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.chdir(BACKEND_DIR)

from app import classifier
from app.category_utils import canonicalize_label, folder_to_label
from app.ndmc_api_client import call_ndmc_api, compare_classifications


TRIAGE_ROOT = BACKEND_DIR / "triage_output"
TRIAGED_DATASET_DIR = TRIAGE_ROOT / "triaged_dataset"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_triage_rows(json_path: Path) -> list[dict[str, Any]]:
    if not json_path.exists():
        raise FileNotFoundError(f"Triage labels JSON not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON list in {json_path}")
    return rows


def load_broken_images(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()

    broken: set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            filepath = (row.get("filepath") or row.get("image") or "").strip()
            if filepath:
                broken.add(filepath.replace("/", "\\"))
    return broken


def resolve_image_path(image_value: str) -> Path:
    image_path = Path(image_value)
    if image_path.parts and image_path.parts[0].lower() == "sorted_dataset":
        image_path = Path(*image_path.parts[1:])
    return TRIAGED_DATASET_DIR / image_path


def collect_live_candidates(sorted_dir: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for folder in sorted(sorted_dir.iterdir()):
        if not folder.is_dir():
            continue
        source_label = folder_to_label(folder.name)
        for image_path in sorted(folder.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTS:
                continue
            candidates.append(
                {
                    "image_path": image_path,
                    "source_folder": folder.name,
                    "source_label": source_label,
                }
            )
    return candidates


def sample_rows(rows: list[dict[str, Any]], sample_size: int, seed: int) -> list[dict[str, Any]]:
    if sample_size <= 0 or sample_size >= len(rows):
        return rows
    rng = random.Random(seed)
    return rng.sample(rows, sample_size)


def build_report_row(row: dict[str, Any], image_path: Path, ndmc_result: dict[str, Any]) -> dict[str, Any]:
    local_label = str(row.get("final_label", "Uncategorized"))
    local_confidence = float(row.get("confidence", 0.0) or 0.0)
    local_result = {"category": local_label, "confidence": local_confidence}
    comparison = compare_classifications(local_result, ndmc_result)
    agreement = bool(comparison.get("comparison", {}).get("match", False))
    ndmc_label = str(ndmc_result.get("category", "Uncategorized"))
    ndmc_confidence = float(ndmc_result.get("confidence", 0.0) or 0.0)

    return {
        "image": row.get("image", ""),
        "source_folder": "",
        "source_label": "",
        "resolved_image_path": str(image_path.relative_to(BACKEND_DIR)),
        "local_label": local_label,
        "local_canonical": canonicalize_label(local_label),
        "local_confidence": f"{local_confidence:.4f}",
        "ndmc_label": ndmc_label,
        "ndmc_canonical": canonicalize_label(ndmc_label),
        "ndmc_confidence": f"{ndmc_confidence:.4f}",
        "ndmc_success": str(bool(ndmc_result.get("success", False))),
        "selected_label": comparison["category"],
        "selected_method": comparison["method"],
        "agreement": str(agreement),
        "comparison_reason": comparison.get("comparison", {}).get("reason", ""),
        "ndmc_error": ndmc_result.get("error", "") or "",
        "local_method": "",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_report(
    sample_size: int,
    seed: int,
    input_json: Path,
    broken_csv: Path,
    output_csv: Path,
    summary_csv: Path,
    live_local: bool,
) -> None:
    report_rows: list[dict[str, Any]] = []
    confusion_counter: Counter[tuple[str, str]] = Counter()
    ndmc_successes = 0
    agreements = 0

    if live_local:
        candidates = collect_live_candidates(TRIAGED_DATASET_DIR)
        if not candidates:
            raise RuntimeError(f"No usable images found under {TRIAGED_DATASET_DIR}")

        sampled = sample_rows(candidates, sample_size, seed)
        local_classifier = classifier.CivicClassifier()

        for item in sampled:
            image_path = item["image_path"]
            local_raw = local_classifier.classify(str(image_path))
            local_label = str(local_raw.get("department", local_raw.get("category", "Uncategorized")))
            local_confidence = float(local_raw.get("confidence", 0.0) or 0.0)
            local_result = {"category": local_label, "confidence": local_confidence}
            ndmc_result = call_ndmc_api(str(image_path))
            comparison = compare_classifications(local_result, ndmc_result)
            agreement = bool(comparison.get("comparison", {}).get("match", False))
            ndmc_label = str(ndmc_result.get("category", "Uncategorized"))
            ndmc_confidence = float(ndmc_result.get("confidence", 0.0) or 0.0)

            report_rows.append(
                {
                    "image": str(image_path.relative_to(BACKEND_DIR)),
                    "source_folder": item["source_folder"],
                    "source_label": item["source_label"],
                    "resolved_image_path": str(image_path.relative_to(BACKEND_DIR)),
                    "local_label": local_label,
                    "local_canonical": canonicalize_label(local_label),
                    "local_confidence": f"{local_confidence:.4f}",
                    "ndmc_label": ndmc_label,
                    "ndmc_canonical": canonicalize_label(ndmc_label),
                    "ndmc_confidence": f"{ndmc_confidence:.4f}",
                    "ndmc_success": str(bool(ndmc_result.get("success", False))),
                    "selected_label": comparison["category"],
                    "selected_method": comparison["method"],
                    "agreement": str(agreement),
                    "comparison_reason": comparison.get("comparison", {}).get("reason", ""),
                    "ndmc_error": ndmc_result.get("error", "") or "",
                    "local_method": str(local_raw.get("method", "")),
                }
            )

            if ndmc_result.get("success", False):
                ndmc_successes += 1
                if agreement:
                    agreements += 1
                else:
                    confusion_counter[(canonicalize_label(local_label), canonicalize_label(ndmc_label))] += 1
    else:
        rows = load_triage_rows(input_json)
        broken_images = load_broken_images(broken_csv)

        candidates: list[dict[str, Any]] = []
        for row in rows:
            image_value = str(row.get("image", "")).strip()
            if not image_value:
                continue
            image_path = resolve_image_path(image_value)
            normalized_key = image_value.replace("/", "\\")
            if normalized_key in broken_images or str(image_path) in broken_images:
                continue
            if image_path.exists():
                candidates.append({"row": row, "image_path": image_path})

        if not candidates:
            raise RuntimeError(f"No usable triage cases found under {TRIAGED_DATASET_DIR}")

        sampled = sample_rows(candidates, sample_size, seed)

        for item in sampled:
            row = item["row"]
            image_path = item["image_path"]
            ndmc_result = call_ndmc_api(str(image_path))
            report_row = build_report_row(row, image_path, ndmc_result)
            report_rows.append(report_row)

            if ndmc_result.get("success", False):
                ndmc_successes += 1
                local_canonical = report_row["local_canonical"]
                ndmc_canonical = report_row["ndmc_canonical"]
                if report_row["agreement"] == "True":
                    agreements += 1
                else:
                    confusion_counter[(local_canonical, ndmc_canonical)] += 1

    report_fields = [
        "image",
        "source_folder",
        "source_label",
        "resolved_image_path",
        "local_label",
        "local_canonical",
        "local_confidence",
        "ndmc_label",
        "ndmc_canonical",
        "ndmc_confidence",
        "ndmc_success",
        "selected_label",
        "selected_method",
        "agreement",
        "comparison_reason",
        "ndmc_error",
        "local_method",
    ]
    write_csv(output_csv, report_rows, report_fields)

    agreement_rate = agreements / ndmc_successes if ndmc_successes else 0.0
    top_confusions = confusion_counter.most_common(5)

    summary_rows: list[dict[str, Any]] = [
        {"metric": "sample_size", "value": len(report_rows), "details": "sampled existing cases"},
        {"metric": "ndmc_successes", "value": ndmc_successes, "details": "successful NDMC responses"},
        {"metric": "agreement_rate", "value": f"{agreement_rate:.4f}", "details": f"{agreements}/{ndmc_successes or 0}"},
    ]
    for index, ((local_label, ndmc_label), count) in enumerate(top_confusions, start=1):
        summary_rows.append(
            {
                "metric": f"top_confusion_{index}",
                "value": count,
                "details": f"{local_label} -> {ndmc_label}",
            }
        )
    if not top_confusions:
        summary_rows.append({"metric": "top_confusion_1", "value": 0, "details": "no mismatches in successful NDMC comparisons"})

    write_csv(summary_csv, summary_rows, ["metric", "value", "details"])

    print(f"Sampled cases: {len(report_rows)}")
    print(f"NDMC successes: {ndmc_successes}")
    print(f"Agreement rate: {agreement_rate:.1%}")
    if top_confusions:
        print("Top confusions:")
        for index, ((local_label, ndmc_label), count) in enumerate(top_confusions, start=1):
            print(f"  {index}. {local_label} -> {ndmc_label}: {count}")
    print(f"Report CSV: {output_csv}")
    print(f"Summary CSV: {summary_csv}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a quick NDMC agreement analysis on existing triage outputs.")
    parser.add_argument("--sample", type=int, default=8, help="Number of existing cases to sample.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling.")
    parser.add_argument(
        "--input-json",
        type=Path,
        default=TRIAGE_ROOT / "triage_labels.json",
        help="Path to the stored triage labels JSON file.",
    )
    parser.add_argument(
        "--broken-csv",
        type=Path,
        default=TRIAGE_ROOT / "broken_images.csv",
        help="Optional CSV listing broken images to skip.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=TRIAGE_ROOT / "ndmc_agreement_report.csv",
        help="Where to write the per-case comparison CSV.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=TRIAGE_ROOT / "ndmc_agreement_summary.csv",
        help="Where to write the summary CSV.",
    )
    parser.add_argument(
        "--live-local",
        action="store_true",
        help="Run the current CivicClassifier on real images instead of using cached triage outputs.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_report(
        sample_size=args.sample,
        seed=args.seed,
        input_json=args.input_json,
        broken_csv=args.broken_csv,
        output_csv=args.output,
        summary_csv=args.summary_output,
        live_local=args.live_local,
    )