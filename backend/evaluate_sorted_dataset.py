"""
evaluate_sorted_dataset.py
CLI: evaluate sorting quality of a triaged civic-image dataset.

Compares the folder-assigned ground-truth labels (derived from directory
structure) against the predicted labels stored in triage_labels.csv and
reports per-category accuracy, confidence statistics, and a full match table.

Usage examples
--------------
  # Full evaluation against default triage output:
  python backend/evaluate_sorted_dataset.py

  # Quick spot-check: sample 20 images per folder
  python backend/evaluate_sorted_dataset.py --sample 20

  # Custom paths:
  python backend/evaluate_sorted_dataset.py \
      --sorted-dir backend/sorted_dataset \
      --labels-csv backend/triage_output/triage_labels.csv \
      --output    backend/evaluation_report_v3.csv \
      --sample 50
"""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path
from typing import List

import pandas as pd

# ---------------------------------------------------------------------------
# Ollama host fix (mirrors automated_triage.py)
# ---------------------------------------------------------------------------
_ollama_host = os.getenv("OLLAMA_HOST", "")
if _ollama_host.startswith("0.0.0.0"):
    _fixed = _ollama_host.replace("0.0.0.0", "127.0.0.1", 1)
    os.environ["OLLAMA_HOST"] = _fixed

try:
    from app.category_utils import folder_to_canonical  # type: ignore
except Exception:  # running outside the backend package context
    def folder_to_canonical(folder_name: str) -> str:  # type: ignore
        """Best-effort: convert a snake_case folder name back to display label."""
        return folder_name.replace("_-_", " - ").replace("_", " ")


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_images_from_sorted_dir(
    sorted_dir: Path, sample: int, seed: int = 42
) -> List[dict]:
    """Walk sorted_dir and return records with ground-truth folder label."""
    random.seed(seed)
    records: List[dict] = []
    for folder in sorted(sorted_dir.iterdir()):
        if not folder.is_dir():
            continue
        images = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]
        if not images:
            continue
        if sample > 0:
            images = random.sample(images, min(sample, len(images)))
        label = folder_to_canonical(folder.name)
        for img in images:
            records.append({"image_path": str(img), "ground_truth_folder": folder.name, "ground_truth_label": label})
    return records


def load_triage_labels(labels_csv: Path) -> pd.DataFrame:
    """Load triage_labels.csv; return empty DataFrame if file not found."""
    if not labels_csv.exists():
        print(f"[warn] Labels CSV not found: {labels_csv} – skipping label comparison.")
        return pd.DataFrame()
    df = pd.read_csv(labels_csv)
    # Normalise the image column to just the filename for join robustness
    df["_image_name"] = df["image"].apply(lambda p: Path(p).name)
    return df


def evaluate(
    sorted_dir: Path,
    labels_csv: Path,
    output_csv: Path,
    sample: int,
) -> None:
    print(f"\n{'='*60}")
    print("  Jan-Sunwai AI – Sorted Dataset Evaluation")
    print(f"{'='*60}")
    print(f"  Sorted dataset : {sorted_dir}")
    print(f"  Labels CSV     : {labels_csv}")
    print(f"  Output report  : {output_csv}")
    print(f"  Sample / folder: {'all' if sample == 0 else sample}")
    print(f"{'='*60}\n")

    if not sorted_dir.exists():
        raise FileNotFoundError(f"Sorted dataset directory not found: {sorted_dir}")

    # 1. Collect ground-truth records from folder structure
    gt_records = collect_images_from_sorted_dir(sorted_dir, sample)
    if not gt_records:
        print("[warn] No images found in the sorted dataset directory.")
        return
    gt_df = pd.DataFrame(gt_records)
    gt_df["_image_name"] = gt_df["image_path"].apply(lambda p: Path(p).name)

    total_images = len(gt_df)
    print(f"Images collected : {total_images}")

    # 2. Per-category image count
    print("\n--- Image count per folder ---")
    counts = gt_df.groupby("ground_truth_folder").size().sort_values(ascending=False)
    for folder, count in counts.items():
        print(f"  {folder:<45} {count:>5}")

    # 3. Merge with triage labels (if available)
    labels_df = load_triage_labels(labels_csv)

    if labels_df.empty:
        # No predictions available – write a counts-only report
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        gt_df.drop(columns=["_image_name"], errors="ignore").to_csv(output_csv, index=False)
        print(f"\n[info] Ground-truth-only report written to {output_csv}")
        return

    merged = gt_df.merge(
        labels_df[["_image_name", "final_label", "confidence", "rationale", "vision_summary", "used_vision_model"]],
        on="_image_name",
        how="left",
    )

    merged["predicted_label"] = merged["final_label"].fillna("(no prediction)")
    merged["confidence"] = pd.to_numeric(merged["confidence"], errors="coerce").fillna(0.0)
    merged["match"] = merged["ground_truth_label"].str.strip() == merged["predicted_label"].str.strip()

    # 4. Overall accuracy
    labelled_mask = merged["predicted_label"] != "(no prediction)"
    labelled = merged[labelled_mask]
    overall_accuracy = labelled["match"].mean() if len(labelled) > 0 else float("nan")
    coverage = labelled_mask.sum() / total_images if total_images > 0 else 0.0

    print(f"\n--- Overall results ---")
    print(f"  Labelled images (have a prediction) : {labelled_mask.sum()} / {total_images} ({coverage:.1%})")
    print(f"  Label agreement (accuracy)          : {overall_accuracy:.1%}" if labelled_mask.any() else "  No predictions to compare.")

    # 5. Per-category breakdown
    if labelled_mask.any():
        print("\n--- Per-category agreement ---")
        cat_stats = (
            labelled.groupby("ground_truth_label")
            .agg(
                n=("match", "count"),
                correct=("match", "sum"),
                avg_confidence=("confidence", "mean"),
            )
            .assign(accuracy=lambda d: d["correct"] / d["n"])
            .sort_values("accuracy")
        )
        print(f"  {'Category':<45} {'N':>5} {'Correct':>8} {'Accuracy':>9} {'Avg Conf':>9}")
        print("  " + "-" * 80)
        for cat, row in cat_stats.iterrows():
            print(
                f"  {str(cat):<45} {int(row['n']):>5} {int(row['correct']):>8}"
                f"  {row['accuracy']:>7.1%}  {row['avg_confidence']:>8.2f}"
            )

    # 6. Confidence distribution
    if labelled_mask.any():
        print("\n--- Confidence distribution (all labelled) ---")
        bins = [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]
        labels = ["0–0.25", "0.25–0.5", "0.5–0.75", "0.75–0.9", "0.9–1.0"]
        labelled = labelled.copy()
        labelled["conf_bin"] = pd.cut(labelled["confidence"], bins=bins, labels=labels, right=True)
        conf_dist = labelled["conf_bin"].value_counts().sort_index()
        for bin_label, cnt in conf_dist.items():
            print(f"  {bin_label}: {cnt}")

    # 7. Write report
    report_df = merged.drop(columns=["_image_name"], errors="ignore").rename(
        columns={
            "image_path": "Filename",
            "ground_truth_folder": "Ground_Truth_Folder",
            "ground_truth_label": "Expected_Label",
            "predicted_label": "Predicted_Canonical",
            "confidence": "Confidence",
            "vision_summary": "Vision_Description",
            "match": "Match",
            "used_vision_model": "Model",
        }
    )
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_csv, index=False)
    print(f"\n✅  Evaluation report written to: {output_csv}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate sorting quality of the triaged civic-image dataset."
    )
    parser.add_argument(
        "--sorted-dir",
        type=Path,
        default=Path("sorted_dataset"),
        help="Path to the sorted/triaged dataset directory (default: sorted_dataset)",
    )
    parser.add_argument(
        "--labels-csv",
        type=Path,
        default=Path("triage_output/triage_labels.csv"),
        help="Path to triage_labels.csv produced by automated_triage.py (default: triage_output/triage_labels.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation_report.csv"),
        help="Where to write the evaluation report CSV (default: evaluation_report.csv)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Sample N images per folder (0 = all images, default: 0)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    evaluate(
        sorted_dir=args.sorted_dir,
        labels_csv=args.labels_csv,
        output_csv=args.output,
        sample=args.sample,
    )
