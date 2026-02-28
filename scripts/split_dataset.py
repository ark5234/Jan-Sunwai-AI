"""
split_dataset.py
────────────────
Splits backend/sorted_dataset/ into N balanced "part" folders for Kaggle upload.

Strategy:
  - Images in EACH department are shuffled randomly, then dealt round-robin
    across parts (like dealing a deck of cards).
  - Every part ends up with ALL departments present and a proportional,
    random slice of each department's images.
  - Parts are roughly equal in size (~1 GB each for a 5 GB dataset).

Output structure:
  sorted_dataset_parts/
    part1/
      Municipal_-_Horticulture/   ← ~⅕ of Horticulture images (random)
      Municipal_-_PWD_Roads/      ← ~⅕ of PWD images (random)
      Municipal_-_Sanitation/
      ...
    part2/
      Municipal_-_Horticulture/   ← next ~⅕ of Horticulture images
      ...

Usage
─────
  python scripts/split_dataset.py            # 5 parts (default)
  python scripts/split_dataset.py --parts 4  # 4 parts
  python scripts/split_dataset.py --dry-run  # preview only, no copying
"""

import argparse
import math
import random
import shutil
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parent.parent
SOURCE_ROOT = WORKSPACE / "backend" / "sorted_dataset"
OUTPUT_ROOT = WORKSPACE / "backend" / "sorted_dataset_parts"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
RANDOM_SEED = 42


def split_dataset(n_parts: int, dry_run: bool) -> None:
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"Source not found: {SOURCE_ROOT}")

    rng = random.Random(RANDOM_SEED)

    # Collect images per department, shuffle each independently
    dept_images: dict[str, list[Path]] = {}
    for folder in sorted(SOURCE_ROOT.iterdir()):
        if not folder.is_dir():
            continue
        imgs = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]
        if not imgs:
            continue
        rng.shuffle(imgs)
        dept_images[folder.name] = imgs

    total = sum(len(v) for v in dept_images.values())
    chunk = math.ceil(total / n_parts)

    print(f"Source     : {SOURCE_ROOT}")
    print(f"Output     : {OUTPUT_ROOT}")
    print(f"Total imgs : {total}  →  {n_parts} parts of ~{chunk} each")
    print(f"Dry-run    : {dry_run}\n")

    # Build assignment: for each dept, deal images round-robin across parts
    # part_buckets[i][dept] = list of images for part i+1
    part_buckets: list[dict[str, list[Path]]] = [{} for _ in range(n_parts)]
    for dept, imgs in dept_images.items():
        per_part = math.ceil(len(imgs) / n_parts)
        for i in range(n_parts):
            batch = imgs[i * per_part : (i + 1) * per_part]
            if batch:
                part_buckets[i][dept] = batch

    # Print summary and optionally copy
    for i, buckets in enumerate(part_buckets):
        part_total = sum(len(v) for v in buckets.values())
        print(f"  part{i + 1}  ({part_total} images)")
        for dept in sorted(buckets):
            n = len(buckets[dept])
            print(f"    {dept:<45} {n:>5}")

        if dry_run:
            continue

        part_dir = OUTPUT_ROOT / f"part{i + 1}"
        for dept, imgs in buckets.items():
            dest_dir = part_dir / dept
            dest_dir.mkdir(parents=True, exist_ok=True)
            for img in imgs:
                dest = dest_dir / img.name
                if dest.exists():
                    counter = 1
                    while dest.exists():
                        dest = dest_dir / f"{img.stem}_{counter}{img.suffix}"
                        counter += 1
                shutil.copy2(img, dest)

        print()

    if not dry_run:
        print(f"\n✅  Done — parts written to {OUTPUT_ROOT}")
        print("     Zip each part folder and upload to Kaggle.")
    else:
        print("\n(Dry-run complete — no files were copied.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split sorted_dataset into N balanced parts for Kaggle upload."
    )
    parser.add_argument("--parts", type=int, default=5, help="Number of parts (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Preview split without copying files")
    args = parser.parse_args()

    split_dataset(n_parts=args.parts, dry_run=args.dry_run)
