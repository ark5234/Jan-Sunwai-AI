import os
import csv
import random
import argparse
from app.classifier import CivicClassifier
from app.category_utils import folder_to_label, canonicalize_label, labels_match
from tqdm import tqdm
from pathlib import Path

# --- CONFIGURATION ---
SORTED_DATASET_ROOT = Path("sorted_dataset")
OUTPUT_FILE = "evaluation_report_v2.csv"


def get_all_images(root_dir):
    image_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                image_files.append(Path(dirpath) / filename)
    return image_files


def get_sampled_images(root_dir: Path, sample_per_folder: int) -> list:
    """Pick up to sample_per_folder random images from each category folder."""
    sampled = []
    for folder in sorted(root_dir.iterdir()):
        if not folder.is_dir():
            continue
        images = [
            p for p in folder.iterdir()
            if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}
        ]
        if not images:
            print(f"  ⚠  {folder.name}: 0 images — skipping")
            continue
        picked = random.sample(images, min(sample_per_folder, len(images)))
        print(f"  {folder.name}: {len(images)} total → sampling {len(picked)}")
        sampled.extend(picked)
    return sampled


def main():
    parser = argparse.ArgumentParser(description="Evaluate sorted dataset with new Ollama pipeline")
    parser.add_argument(
        "--sample", type=int, default=20,
        help="Images to sample per folder (default: 20). Use 0 to run ALL images."
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducible sampling (default: 42)"
    )
    args = parser.parse_args()

    random.seed(args.seed)

    print("--- Starting Evaluation on SORTED Dataset ---")

    if not SORTED_DATASET_ROOT.exists():
        print(f"❌ Sorted dataset not found at {SORTED_DATASET_ROOT}")
        return

    # 1. Load classifier (no model to load — just initialises the class)
    classifier = CivicClassifier()
    print("✅ Classifier ready (Ollama pipeline)")

    # 2. Find images
    if args.sample == 0:
        print("\nMode: FULL dataset (this will take many hours)")
        all_images = get_all_images(SORTED_DATASET_ROOT)
    else:
        print(f"\nMode: SAMPLE — {args.sample} images per folder")
        all_images = get_sampled_images(SORTED_DATASET_ROOT, args.sample)

    print(f"\nTotal images to evaluate: {len(all_images)}")
    est_minutes = len(all_images) * 15 / 60
    print(f"Estimated time: ~{est_minutes:.0f} minutes\n")

    # 3. Run evaluation
    headers = [
        "Filename",
        "Ground_Truth_Folder",
        "Expected_Label",
        "Predicted_Dept",
        "Predicted_Canonical",
        "Vision_Description",
        "Confidence",
        "Match",
    ]

    correct = 0
    total = 0
    mismatches = []

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for img_path in tqdm(all_images, desc="Evaluating"):
            try:
                folder_name   = img_path.parent.name
                absolute_path = str(img_path.resolve())

                result = classifier.classify(absolute_path)

                expected_label  = folder_to_label(folder_name)
                pred_dept       = result.get('department', 'Uncategorized')
                pred_canonical  = canonicalize_label(pred_dept)
                vision_desc     = result.get('vision_description', result.get('label', ''))
                pred_conf       = result.get('confidence', 0.0)
                is_match        = labels_match(expected_label, pred_canonical)

                if is_match:
                    correct += 1
                else:
                    mismatches.append({
                        "file":      img_path.name,
                        "folder":    folder_name,
                        "expected":  expected_label,
                        "predicted": pred_canonical,
                        "vision":    vision_desc,
                    })

                total += 1

                writer.writerow({
                    "Filename":            img_path.name,
                    "Ground_Truth_Folder": folder_name,
                    "Expected_Label":      expected_label,
                    "Predicted_Dept":      pred_dept,
                    "Predicted_Canonical": pred_canonical,
                    "Vision_Description":  vision_desc,
                    "Confidence":          round(pred_conf, 3),
                    "Match":               is_match,
                })

            except Exception as e:
                print(f"\n⚠  Skipped {img_path.name}: {e}")

    # 4. Print summary
    print(f"\n✅ Evaluation complete  →  {OUTPUT_FILE}")
    if total > 0:
        accuracy = correct / total * 100
        print(f"Accuracy  : {accuracy:.1f}%  ({correct}/{total} correct)")
        print(f"Mismatches: {len(mismatches)}")

        if mismatches:
            print("\n--- Mismatched Images (first 20 shown) ---")
            for m in mismatches[:20]:
                print(f"  [{m['folder']}]  {m['file']}")
                print(f"    Expected  : {m['expected']}")
                print(f"    Predicted : {m['predicted']}")
                print(f"    AI saw    : {m['vision']}")
                print()

        # Per-folder accuracy
        print("--- Per-Folder Accuracy ---")
        from collections import defaultdict
        per_folder: dict = defaultdict(lambda: {"correct": 0, "total": 0})
        import csv as _csv
        with open(OUTPUT_FILE, newline='', encoding='utf-8') as rf:
            for row in _csv.DictReader(rf):
                folder = row["Ground_Truth_Folder"]
                per_folder[folder]["total"] += 1
                if row["Match"] == "True":
                    per_folder[folder]["correct"] += 1
        for folder, counts in sorted(per_folder.items()):
            pct = counts["correct"] / counts["total"] * 100 if counts["total"] else 0
            print(f"  {folder:<40} {pct:5.1f}%  ({counts['correct']}/{counts['total']})")


if __name__ == "__main__":
    main()
