import os
import csv
from PIL import Image
from app.classifier import CivicClassifier
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

def main():
    print("--- 🚀 Starting Evaluation on SORTED Dataset ---")
    
    if not SORTED_DATASET_ROOT.exists():
        print(f"❌ Sorted dataset not found at {SORTED_DATASET_ROOT}")
        print("Please run 'python sort_dataset.py' first.")
        return

    # 1. Load Model
    try:
        classifier = CivicClassifier()
        print("✅ Model Loaded Successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # 2. Find Images
    all_images = get_all_images(SORTED_DATASET_ROOT)
    print(f"Found {len(all_images)} images.")

    # 3. Setup CSV headers
    headers = ["Filename", "Ground_Truth_Folder", "Predicted_Dept", "Predicted_Label", "Confidence", "Match"]
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        correct = 0
        total = 0

        # Iterate
        for img_path in tqdm(all_images):
            try:
                # Ground Truth is the folder name
                # Folder: Municipal_-_PWD_Roads -> Category: Municipal - PWD (Roads)
                folder_name = img_path.parent.name
                
                # Simple heuristic to revert "Safe Name" to "Category Name"
                # This isn't perfect but allows loose matching.
                # Or we just check if the prediction helps.
                
                # --- CLASSIFY ---
                image = Image.open(img_path)
                result = classifier.classify(image)
                
                pred_dept = result['department']
                pred_label = result.get('label', result.get('description', 'Unknown'))
                pred_conf = result['confidence']

                # Normalize for comparison
                # Folder: "Municipal_-_PWD_Roads"
                # Pred: "Municipal - PWD (Roads)"
                
                normalized_folder = folder_name.replace("_", " ").lower()
                normalized_pred = pred_dept.replace("-", " ").replace("(", "").replace(")", "").lower()
                
                # Check match (loose string match)
                # e.g. "manual - sanitation" vs "sanitation"
                
                # Better approach: check if key parts of prediction exist in folder name
                # Folder: Municipal_-_Sanitation
                # Pred: Municipal - Sanitation
                
                is_match = False
                
                # Convert "Municipal_-_PWD_Roads" -> "Municipal - PWD (Roads)" approx
                # We can just use the label map from classifier if we really want strictness, 
                # but string similarity is often enough for reports.
                
                if pred_dept.replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and") == folder_name:
                    is_match = True
                
                # Fallback check
                if not is_match:
                    # check if "Sanitation" is in both
                    parts = pred_dept.split("-")
                    main_part = parts[-1].strip().lower() # e.g. sanitation
                    if main_part in normalized_folder:
                        is_match = True

                if is_match:
                    correct += 1
                
                total += 1

                writer.writerow({
                    "Filename": img_path.name,
                    "Ground_Truth_Folder": folder_name,
                    "Predicted_Dept": pred_dept,
                    "Predicted_Label": pred_label,
                    "Confidence": pred_conf,
                    "Match": is_match
                })
                
            except Exception as e:
                print(f"Error skipping {img_path}: {e}")

    print(f"Evaluation Complete. Report saved to {OUTPUT_FILE}")
    if total > 0:
        print(f"Accuracy: {correct/total*100:.2f}% ({correct}/{total})")

if __name__ == "__main__":
    main()
