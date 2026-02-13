import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

import ollama
import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm
from transformers import CLIPModel, CLIPProcessor

try:
    from cleanvision import Imagelab
except Exception:
    Imagelab = None


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

CATEGORY_PROMPTS: Dict[str, str] = {
    "Municipal - PWD (Roads)": "a photo of a pothole, broken road, damaged pavement, or footpath issue",
    "Municipal - Sanitation": "a photo of overflowing garbage, trash pile, public toilet filth, or waste issue",
    "Municipal - Horticulture": "a photo of fallen tree, unmaintained park, dry plants, or damaged greenery",
    "Municipal - Street Lighting": "a photo of a broken streetlight, non-functional street lamp, or dark street",
    "Municipal - Water & Sewerage": "a photo of water leakage, blocked drain, sewer overflow, or flooded road",
    "Utility - Power (DISCOM)": "a photo of dangling electric wire, open transformer, exposed power cable",
    "State Transport": "a photo of damaged bus stop, broken bus shelter, or state transport infrastructure issue",
    "Pollution Control Board": "a photo of air pollution, smoke emission, industrial dumping, or burning waste",
    "Police - Local Law Enforcement": "a photo of encroachment, illegal parking, public nuisance, or unlawful occupation",
    "Police - Traffic": "a photo of traffic signal failure, traffic jam, intersection blockage, or road obstruction",
}


def list_images(root: Path) -> List[Path]:
    return [p for p in root.rglob("*") if p.suffix.lower() in IMAGE_EXTS]


def split_valid_and_broken_images(images: List[Path]) -> Tuple[List[Path], List[Path]]:
    valid: List[Path] = []
    broken: List[Path] = []
    for p in tqdm(images, desc="Validating images", leave=False):
        try:
            with Image.open(p) as img:
                img.verify()
            valid.append(p)
        except Exception:
            broken.append(p)
    return valid, broken


def stage_valid_dataset_for_audit(valid_images: List[Path], dataset_dir: Path, work_dir: Path) -> Path:
    staged_root = work_dir / "_audit_valid_dataset"
    if staged_root.exists():
        shutil.rmtree(staged_root)
    staged_root.mkdir(parents=True, exist_ok=True)

    for src in tqdm(valid_images, desc="Staging valid images", leave=False):
        rel = src.relative_to(dataset_dir)
        dst = staged_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, dst)
        except Exception:
            shutil.copy2(src, dst)

    return staged_root


def resolve_dataset_dir(dataset_dir: Path) -> Path:
    if dataset_dir.exists() and list_images(dataset_dir):
        return dataset_dir

    candidates = [
        Path("sorted_dataset"),
        Path("dataset"),
        Path("triage_output") / "triaged_dataset",
    ]

    for candidate in candidates:
        if candidate.exists() and list_images(candidate):
            print(f"⚠️ No images found in '{dataset_dir}'. Using '{candidate}' instead.")
            return candidate

    return dataset_dir


def safe_dirname(label: str) -> str:
    return label.replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and")


def run_cleanvision_audit(dataset_dir: Path, prune_ratio: float, work_dir: Path) -> Tuple[List[Path], List[Path], pd.DataFrame]:
    images = list_images(dataset_dir)
    if not images:
        return [], [], pd.DataFrame()

    valid_images, broken_images = split_valid_and_broken_images(images)
    if broken_images:
        print(f"⚠️ Skipping {len(broken_images)} unreadable image(s).")
        broken_df = pd.DataFrame({"filepath": [str(p) for p in broken_images], "issue_count": 999, "issue_type": "broken_file"})
        broken_csv = work_dir / "broken_images.csv"
        broken_df.to_csv(broken_csv, index=False)
        print(f"Broken image report: {broken_csv}")

    if not valid_images:
        return [], broken_images, pd.DataFrame({"filepath": [str(p) for p in broken_images], "issue_count": 999, "issue_type": "broken_file"})

    if Imagelab is None:
        print("⚠️ CleanVision not installed. Skipping audit; all images will be retained.")
        return valid_images, broken_images, pd.DataFrame({"filepath": [str(p) for p in valid_images], "issue_count": 0})

    print("🔎 Running CleanVision audit...")
    staged_dataset_dir = stage_valid_dataset_for_audit(valid_images, dataset_dir, work_dir)
    imagelab = Imagelab(data_path=str(staged_dataset_dir))
    try:
        imagelab.find_issues()
    except Exception as e:
        print(f"⚠️ CleanVision failed ({e}). Continuing without pruning.")
        fallback_df = pd.DataFrame({"filepath": [str(p) for p in valid_images], "issue_count": 0})
        return valid_images, broken_images, fallback_df

    issues_df = imagelab.issues.copy()
    if issues_df.empty:
        return valid_images, broken_images, pd.DataFrame({"filepath": [str(p) for p in valid_images], "issue_count": 0})

    bool_cols = [c for c in issues_df.columns if c.startswith("is_")]
    if bool_cols:
        issues_df["issue_count"] = issues_df[bool_cols].fillna(False).astype(bool).sum(axis=1)
    else:
        issues_df["issue_count"] = 0

    if "given_label" in issues_df.columns:
        issues_df = issues_df.drop(columns=["given_label"])

    path_col = None
    for candidate in ["filepath", "image", "filename"]:
        if candidate in issues_df.columns:
            path_col = candidate
            break

    if path_col is None:
        issues_df["filepath"] = [str(p) for p in valid_images]
        path_col = "filepath"

    issues_df[path_col] = issues_df[path_col].astype(str)
    issues_df = issues_df.sort_values("issue_count", ascending=False).reset_index(drop=True)

    prune_count = int(len(issues_df) * prune_ratio)
    bad_df = issues_df.head(prune_count)
    keep_df = issues_df.iloc[prune_count:]

    rejected = []
    for raw_path in bad_df[path_col].tolist():
        p = Path(raw_path)
        if not p.is_absolute():
            p = staged_dataset_dir / p
        try:
            p = dataset_dir / p.relative_to(staged_dataset_dir)
        except Exception:
            pass
        if p.exists():
            rejected.append(p)

    kept = []
    for raw_path in keep_df[path_col].tolist():
        p = Path(raw_path)
        if not p.is_absolute():
            p = staged_dataset_dir / p
        try:
            p = dataset_dir / p.relative_to(staged_dataset_dir)
        except Exception:
            pass
        if p.exists():
            kept.append(p)

    rejected_dir = work_dir / "audit_rejected"
    rejected_dir.mkdir(parents=True, exist_ok=True)
    for p in rejected:
        target = rejected_dir / p.name
        suffix_counter = 1
        while target.exists():
            target = rejected_dir / f"{target.stem}_{suffix_counter}{target.suffix}"
            suffix_counter += 1
        shutil.copy2(p, target)

    rejected = rejected + broken_images
    return kept, rejected, issues_df


class ClipSorter:
    def __init__(self, category_prompts: Dict[str, str]):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.categories = list(category_prompts.keys())
        self.prompts = [category_prompts[c] for c in self.categories]
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        getattr(self.model, "to")(self.device)
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    def classify(self, image_path: Path) -> Tuple[str, float, float, List[Tuple[str, float]]]:
        image = Image.open(image_path).convert("RGB")
        processor_kwargs: Dict[str, Any] = {
            "text": self.prompts,
            "images": image,
            "return_tensors": "pt",
            "padding": True,
        }
        inputs = self.processor(**processor_kwargs)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).squeeze(0)

        scored = [(self.categories[i], float(probs[i].item())) for i in range(len(self.categories))]
        scored.sort(key=lambda x: x[1], reverse=True)

        top_label, top_score = scored[0]
        second_score = scored[1][1] if len(scored) > 1 else 0.0
        margin = top_score - second_score
        return top_label, top_score, margin, scored


def llava_label(image_path: Path, categories: List[str]) -> str:
    choices = ", ".join(categories)
    prompt = (
        "Identify the civic issue category in this image. "
        f"Choose exactly one from: {choices}. "
        "Reply with only the exact category text."
    )
    try:
        response = ollama.generate(model="llava", prompt=prompt, images=[str(image_path)])
        text = response.get("response", "").strip()
        for c in categories:
            if text.lower() == c.lower() or c.lower() in text.lower():
                return c
        return "Uncategorized"
    except Exception:
        return "Uncategorized"


def run_pipeline(
    dataset_dir: Path,
    output_dir: Path,
    prune_ratio: float,
    clip_min_conf: float,
    clip_min_margin: float,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    triage_dir = output_dir / "triaged_dataset"
    triage_dir.mkdir(parents=True, exist_ok=True)

    dataset_dir = resolve_dataset_dir(dataset_dir)

    print("\n=== STEP 1: Automated Cleaning (Audit) ===")
    kept_images, rejected_images, issues_df = run_cleanvision_audit(dataset_dir, prune_ratio, output_dir)
    print(f"Total images: {len(kept_images) + len(rejected_images)}")
    print(f"Rejected by audit: {len(rejected_images)}")
    print(f"Kept for labeling: {len(kept_images)}")

    if not kept_images:
        print("⚠️ No images available after audit. Exiting without CLIP/LLaVA stages.")
        audit_csv = output_dir / "audit_issues.csv"
        labels_csv = output_dir / "triage_labels.csv"
        review_csv = output_dir / "review_queue.csv"
        labels_json = output_dir / "triage_labels.json"

        issues_df.to_csv(audit_csv, index=False)
        pd.DataFrame([]).to_csv(labels_csv, index=False)
        pd.DataFrame([]).to_csv(review_csv, index=False)
        with open(labels_json, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

        print("✅ Empty reports generated")
        print(f"- Audit report: {audit_csv}")
        print(f"- Label report: {labels_csv}")
        print(f"- Review queue: {review_csv}")
        print(f"- JSON export: {labels_json}")
        return

    print("\n=== STEP 2: Zero-Shot Sorting (CLIP) ===")
    sorter = ClipSorter(CATEGORY_PROMPTS)

    for cat in list(CATEGORY_PROMPTS.keys()) + ["Uncategorized"]:
        (triage_dir / safe_dirname(cat)).mkdir(parents=True, exist_ok=True)

    records = []
    uncertain_records = []

    for image_path in tqdm(kept_images, desc="CLIP triage"):
        top_label, top_score, margin, ranked = sorter.classify(image_path)
        needs_fallback = (top_score < clip_min_conf) or (margin < clip_min_margin)

        final_label = top_label
        method = "clip"

        if needs_fallback:
            method = "llava"
            final_label = llava_label(image_path, list(CATEGORY_PROMPTS.keys()))
            uncertain_records.append(
                {
                    "image": str(image_path),
                    "clip_top_label": top_label,
                    "clip_top_score": top_score,
                    "clip_margin": margin,
                    "llava_label": final_label,
                }
            )

        if final_label not in CATEGORY_PROMPTS:
            final_label = "Uncategorized"

        target_dir = triage_dir / safe_dirname(final_label)
        target_path = target_dir / image_path.name
        suffix_counter = 1
        while target_path.exists():
            target_path = target_dir / f"{target_path.stem}_{suffix_counter}{target_path.suffix}"
            suffix_counter += 1
        shutil.copy2(image_path, target_path)

        records.append(
            {
                "image": str(image_path),
                "final_label": final_label,
                "method": method,
                "clip_top_label": top_label,
                "clip_top_score": top_score,
                "clip_margin": margin,
                "top3": json.dumps(ranked[:3]),
            }
        )

    print("\n=== STEP 3: Generative Labeling (LLaVA fallback) ===")
    print(f"Fallback-triggered images: {len(uncertain_records)}")

    print("\n=== STEP 4: Human-in-the-Loop Validation Artifacts ===")
    audit_csv = output_dir / "audit_issues.csv"
    labels_csv = output_dir / "triage_labels.csv"
    review_csv = output_dir / "review_queue.csv"
    labels_json = output_dir / "triage_labels.json"

    issues_df.to_csv(audit_csv, index=False)
    pd.DataFrame(records).to_csv(labels_csv, index=False)
    pd.DataFrame(uncertain_records).to_csv(review_csv, index=False)

    with open(labels_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print("✅ Pipeline complete")
    print(f"- Triaged folders: {triage_dir}")
    print(f"- Audit report: {audit_csv}")
    print(f"- Label report: {labels_csv}")
    print(f"- Review queue: {review_csv}")
    print(f"- JSON export: {labels_json}")


def parse_args():
    parser = argparse.ArgumentParser(description="Automated Triage Pipeline for Civic Image Dataset")
    parser.add_argument("--dataset-dir", type=Path, default=Path("dataset"), help="Path to raw image dataset")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("triage_output"),
        help="Output directory for triaged data + reports",
    )
    parser.add_argument("--prune-ratio", type=float, default=0.15, help="Fraction of worst images to prune (0.1 to 0.2 recommended)")
    parser.add_argument("--clip-min-conf", type=float, default=0.45, help="CLIP confidence threshold for direct auto-label")
    parser.add_argument("--clip-min-margin", type=float, default=0.08, help="Top1-Top2 margin threshold for uncertainty")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        prune_ratio=args.prune_ratio,
        clip_min_conf=args.clip_min_conf,
        clip_min_margin=args.clip_min_margin,
    )
