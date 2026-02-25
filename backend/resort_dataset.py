"""
resort_dataset.py — Re-sort sorted_dataset using the Ollama two-step AI pipeline.

Problem:
    sorted_dataset/ was originally sorted by CLIP (low accuracy).
    This script runs every image through the real CivicClassifier
    and MOVES it into ai_sorted_dataset/ under the correct folder.
    (No copies made — assumes you have a backup of the originals.)

Usage:
    python backend/resort_dataset.py                    # process all ~23K images
    python backend/resort_dataset.py --sample 10        # 10 per folder (quick test)

Output:
    backend/ai_sorted_dataset/<Category>/               # correctly sorted images
    backend/ai_resort_report.csv                        # full move history (old path → new path)
"""

import argparse
import csv
import random
import shutil
import sys
from pathlib import Path

from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent
SOURCE_DIR  = BACKEND_DIR / "sorted_dataset"
OUTPUT_DIR  = BACKEND_DIR / "ai_sorted_dataset"
REPORT_FILE = BACKEND_DIR / "ai_resort_report.csv"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_images(source: Path, sample: int | None) -> list[Path]:
    images: list[Path] = []
    for folder in sorted(source.iterdir()):
        if not folder.is_dir():
            continue
        folder_images = [
            p for p in folder.iterdir()
            if p.suffix.lower() in IMAGE_EXTS
        ]
        if not folder_images:
            print(f"  ⚠  {folder.name}: no images — skipping")
            continue
        if sample:
            folder_images = random.sample(folder_images, min(sample, len(folder_images)))
        print(f"  {folder.name}: {len(folder_images)} images queued")
        images.extend(folder_images)
    return images


def safe_move(src: Path, dest_dir: Path) -> Path:
    """Move src into dest_dir, avoiding filename collisions."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        stem, suffix = src.stem, src.suffix
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
    shutil.move(str(src), dest)
    return dest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-sort sorted_dataset using the Ollama AI pipeline."
    )
    parser.add_argument(
        "--sample", type=int, default=0,
        help="Images per folder to process (0 = all). Use a small number for a quick test."
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducible sampling (default: 42)"
    )
    parser.add_argument(
        "--source", type=str, default=str(SOURCE_DIR),
        help="Path to source folder containing category sub-folders."
    )
    parser.add_argument(
        "--output", type=str, default=str(OUTPUT_DIR),
        help="Path to write the re-sorted dataset."
    )
    args = parser.parse_args()

    random.seed(args.seed)

    source = Path(args.source)
    output = Path(args.output)

    if not source.exists():
        print(f"❌ Source not found: {source}")
        sys.exit(1)

    # Import here so the script can be called from project root or backend/
    try:
        from app.classifier import CivicClassifier
        from app.category_utils import safe_dirname
    except ModuleNotFoundError:
        # Try adding backend to sys.path
        sys.path.insert(0, str(BACKEND_DIR))
        from app.classifier import CivicClassifier
        from app.category_utils import safe_dirname

    print("=" * 60)
    print("Jan-Sunwai AI — Dataset Re-Sorter")
    print("=" * 60)
    print(f"Source : {source}")
    print(f"Output : {output}")
    print()

    sample_per_folder = args.sample if args.sample > 0 else None
    images = collect_images(source, sample_per_folder)

    total = len(images)
    if total == 0:
        print("❌ No images found.")
        sys.exit(1)

    est_hours = total * 150 / 3600   # ~150 s per image on RTX 3050 4 GB
    print(f"\nTotal images  : {total}")
    print(f"Estimated time: ~{est_hours:.1f} h  ({est_hours * 60:.0f} min)")
    if total > 500:
        print("💡 Tip: use --sample 10 first to verify everything works correctly")
    print()

    classifier = CivicClassifier()

    headers = [
        "filename", "source_path", "source_folder", "original_label",
        "ai_label", "confidence", "vision_description", "dest_path",
    ]

    moved = 0
    same  = 0
    error = 0

    output.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for img_path in tqdm(images, desc="Re-sorting", unit="img"):
            original_folder = img_path.parent.name
            original_label  = original_folder.replace("_", " ").replace("  ", " - ")

            result = classifier.classify(str(img_path))

            ai_label    = result.get("department", "Uncategorized")
            confidence  = result.get("confidence", 0.0)
            vision_desc = result.get("vision_description", result.get("label", ""))

            # Low-confidence or Unknown → send to Uncategorized for human review
            if confidence <= 0.4 or ai_label in ("Unknown", ""):
                ai_label = "Uncategorized"

            source_path_str = str(img_path.resolve())
            dest_folder     = output / safe_dirname(ai_label)
            dest_path       = safe_move(img_path, dest_folder)

            if ai_label != original_label:
                moved += 1
            else:
                same += 1

            writer.writerow({
                "filename":           img_path.name,
                "source_path":        source_path_str,
                "source_folder":      original_folder,
                "original_label":     original_label,
                "ai_label":           ai_label,
                "confidence":         confidence,
                "vision_description": vision_desc,
                "dest_path":          str(dest_path.resolve()),
            })

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print()
    print("=" * 60)
    print("✅ Re-sort complete  (originals moved — check your backup if you need to undo)")
    print(f"   Images processed : {total}")
    print(f"   Re-labelled      : {moved}  ({moved/total*100:.1f}%)")
    print(f"   Label confirmed  : {same}   ({same/total*100:.1f}%)")
    if error:
        print(f"   Errors           : {error}")
    print(f"   Output folder    : {output}")
    print(f"   Move history CSV : {REPORT_FILE}  (columns: source_path → dest_path)")
    print()

    # Show per-category counts
    print("Output folder sizes:")
    for cat_dir in sorted(output.iterdir()):
        if cat_dir.is_dir():
            n = len(list(cat_dir.iterdir()))
            print(f"   {cat_dir.name:<45} {n:>5} images")


if __name__ == "__main__":
    main()
