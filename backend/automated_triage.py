import argparse
import json
import os
import shutil
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import ollama
import pandas as pd
from PIL import Image
from tqdm import tqdm
from app.category_utils import safe_dirname

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


class _RemovedInNewPipeline:
    pass  # ClipSorter removed — pipeline now uses Ollama vision+reasoning exclusively.


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


# ── Keyword fallback: scan description text for civic keywords ────────────
_KEYWORD_FALLBACK_RULES: list[tuple[list[str], str]] = [
    (["pothole", "road damage", "cracked road", "broken road", "damaged road",
      "damaged pavement", "broken pavement", "footpath damage", "manhole"],
     "Municipal - PWD (Roads)"),
    (["waterlog", "flooded", "flood", "drain overflow", "sewer overflow",
      "pipe leak", "water gushing", "stagnant water", "blocked drain",
      "drainage problem"],
     "Municipal - Water & Sewerage"),
    (["garbage", "trash", "waste", "litter", "dump", "rubbish", "overflowing bin"],
     "Municipal - Sanitation"),
    (["fallen tree", "uprooted tree", "overgrown", "dead plant", "broken branch",
      "tree blocking"],
     "Municipal - Horticulture"),
    (["street light", "lamp post", "unlit road", "broken light", "dark road"],
     "Municipal - Street Lighting"),
    (["dangling wire", "hanging wire", "open transformer", "fallen electric pole",
      "exposed wire", "power cable"],
     "Utility - Power (DISCOM)"),
    (["smoke", "burning", "industrial waste", "air pollution", "open burning"],
     "Pollution Control Board"),
    (["traffic signal", "signal failure", "traffic jam", "road blockage"],
     "Police - Traffic"),
    (["illegal parking", "encroachment", "footpath blocked", "public nuisance"],
     "Police - Local Law Enforcement"),
    (["bus shelter", "state bus", "transport terminal"],
     "State Transport"),
]


def _keyword_fallback(description: str) -> str:
    """Scan text for civic keywords and return best matching category."""
    desc = description.lower()
    for keywords, category in _KEYWORD_FALLBACK_RULES:
        if any(kw in desc for kw in keywords):
            return category
    return "Uncategorized"


def vision_describe(image_path: Path, categories: List[str], model: str) -> Dict[str, Any]:
    schema = {
        "summary": "short factual description",
        "main_action": "single phrase",
        "setting": "single phrase",
        "hazards": ["hazard1", "hazard2"],
        "candidate_labels": categories[:3],
    }
    prompt = (
        "You are a civic-issue vision analyst. Analyze the image and return strict JSON only.\n"
        f"Allowed civic labels: {json.dumps(categories)}\n"
        f"JSON schema example: {json.dumps(schema)}\n"
        "Rules: no markdown, no explanation outside JSON, keep summary under 30 words, "
        "candidate_labels must be chosen only from the allowed labels."
    )

    response = ollama.generate(model=model, prompt=prompt, images=[str(image_path)], format="json")
    payload = _extract_json(response.get("response", ""))

    if not payload:
        return {
            "summary": "Unable to extract structured vision description",
            "main_action": "unknown",
            "setting": "unknown",
            "hazards": [],
            "candidate_labels": [],
        }

    payload.setdefault("summary", "")
    payload.setdefault("main_action", "unknown")
    payload.setdefault("setting", "unknown")
    payload.setdefault("hazards", [])
    payload.setdefault("candidate_labels", [])
    return payload


def reason_label(
    vision_payload: Dict[str, Any],
    category_prompts: Dict[str, str],
    model: str,
) -> Dict[str, Any]:
    definitions = [{"label": k, "definition": v} for k, v in category_prompts.items()]
    prompt = (
        "You are a strict classification judge. Pick the single best civic category.\n"
        f"Category definitions: {json.dumps(definitions)}\n"
        f"Vision analysis: {json.dumps(vision_payload)}\n"
        "Return strict JSON only with keys: label, confidence, rationale.\n"
        "confidence must be a number between 0 and 1."
    )

    response = ollama.generate(model=model, prompt=prompt, format="json")
    payload = _extract_json(response.get("response", ""))

    label = str(payload.get("label", "Uncategorized")) if payload else "Uncategorized"
    confidence = payload.get("confidence", 0.0) if payload else 0.0
    rationale = str(payload.get("rationale", "")) if payload else ""

    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.0

    return {"label": label, "confidence": confidence, "rationale": rationale}


def vision_reasoning_label(
    image_path: Path,
    category_prompts: Dict[str, str],
    vision_model: str,
    reasoner_model: str,
) -> Dict[str, Any]:
    categories = list(category_prompts.keys())
    try:
        used_vision_model = vision_model
        try:
            vision_payload = vision_describe(image_path, categories, used_vision_model)
        except Exception as vision_err:
            raise RuntimeError(f"Vision step failed for {image_path}: {vision_err}") from vision_err
        judged = reason_label(vision_payload, category_prompts, reasoner_model)
        label = judged.get("label", "Uncategorized")
        if label not in categories:
            label = "Uncategorized"
        method = "vision_reasoning"
        # Keyword fallback if reasoning returned Uncategorized
        if label == "Uncategorized":
            fallback_text = " ".join([
                vision_payload.get("summary", ""),
                vision_payload.get("main_action", ""),
                vision_payload.get("setting", ""),
                " ".join(vision_payload.get("hazards", [])),
            ])
            keyword_result = _keyword_fallback(fallback_text)
            if keyword_result != "Uncategorized":
                label = keyword_result
                method = "keyword_fallback"
        return {
            "label": label,
            "confidence": float(judged.get("confidence", 0.0)),
            "rationale": judged.get("rationale", ""),
            "method": method,
            "used_vision_model": used_vision_model,
            "vision_summary": vision_payload.get("summary", ""),
            "vision_payload": vision_payload,
        }
    except Exception:
        return {
            "label": "Uncategorized",
            "confidence": 0.0,
            "rationale": "vision_reasoning_failed",
            "used_vision_model": vision_model,
            "vision_summary": "",
            "vision_payload": {},
        }


def run_pipeline(
    dataset_dir: Path,
    output_dir: Path,
    prune_ratio: float,
    vision_model: str,
    reasoner_model: str,
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
        print("⚠️ No images available after audit. Exiting without Ollama AI pipeline stages.")
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

    print("\n=== STEP 2: Vision-to-Reasoning Labeling (Ollama) ===")
    print(f"Vision model:    {vision_model}")
    print(f"Reasoner model:  {reasoner_model}")

    for cat in list(CATEGORY_PROMPTS.keys()) + ["Uncategorized"]:
        (triage_dir / safe_dirname(cat)).mkdir(parents=True, exist_ok=True)

    records = []

    for image_path in tqdm(kept_images, desc="Ollama triage"):
        vr = vision_reasoning_label(
            image_path=image_path,
            category_prompts=CATEGORY_PROMPTS,
            vision_model=vision_model,
            reasoner_model=reasoner_model,
        )
        final_label = vr.get("label", "Uncategorized")
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
                "method": "vision_reasoning",
                "confidence": vr.get("confidence", 0.0),
                "rationale": vr.get("rationale", ""),
                "vision_summary": vr.get("vision_summary", ""),
                "used_vision_model": vr.get("used_vision_model", vision_model),
            }
        )

    print("\n=== STEP 3: Human-in-the-Loop Validation Artifacts ===")
    audit_csv = output_dir / "audit_issues.csv"
    labels_csv = output_dir / "triage_labels.csv"
    review_csv = output_dir / "review_queue.csv"
    labels_json = output_dir / "triage_labels.json"

    issues_df.to_csv(audit_csv, index=False)
    pd.DataFrame(records).to_csv(labels_csv, index=False)
    pd.DataFrame([]).to_csv(review_csv, index=False)   # review queue now auto-handled by confidence field

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
    parser.add_argument("--vision-model", type=str, default="qwen2.5vl:3b", help="Ollama vision model for image narration")
    parser.add_argument("--reasoner-model", type=str, default="llama3.2:1b", help="Ollama text model for folder reasoning")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        prune_ratio=args.prune_ratio,
        vision_model=args.vision_model,
        reasoner_model=args.reasoner_model,
    )
