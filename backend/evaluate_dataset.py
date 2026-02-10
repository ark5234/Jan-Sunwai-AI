import os
import csv
import time
from PIL import Image
from app.classifier import CivicClassifier
from tqdm import tqdm  # You might need to install this: pip install tqdm

# --- CONFIGURATION ---
DATASET_ROOT = os.path.join(os.path.dirname(__file__), "dataset")
OUTPUT_FILE = "evaluation_full_report.csv"
LOW_CONFIDENCE_FILE = "evaluation_review_needed.csv"
CONFIDENCE_THRESHOLD = 60.0  # Flag anything below 60%

# Map Top-Level Folder Names to our Classifier Departments
FOLDER_MAP = {
    "Air_Pollution": ["Pollution Control Dept", "Sanitation Dept", "Civil Engineering Dept"], # Overlap
    "CIVIL_ENGINEERING_DEPARTMENT-I": ["Civil Engineering Dept", "Drainage Dept"],
    "Commercial_Department": ["Electricity Dept"], # Often bill/meter issues
    "Electricity_-I": ["Electricity Dept"],
    "Enforcement_Department_(North)": ["Enforcement Dept"],
    "Enforcement_Department_(South)": ["Enforcement Dept"],
    "Horticulture_Department": ["Horticulture Dept"],
    "Metro_Waste": ["Sanitation Dept", "Pollution Control Dept"],
    "Monsoon": ["Drainage Dept", "VBD Dept"],
    "NDMC_Municipal_Housing": ["Civil Engineering Dept"],
    "Welfare_Department": ["Civil Engineering Dept"] # Generic
}

def get_all_images(root_dir):
    image_files = []
    print(f"Scanning {root_dir}...")
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(dirpath, filename))
    return image_files

def main():
    print("--- 🚀 Starting Full Dataset Evaluation ---")
    
    # 1. Load Model
    try:
        classifier = CivicClassifier()
        print("✅ Model Loaded Successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # 2. Find Images
    all_images = get_all_images(DATASET_ROOT)
    total_images = len(all_images)
    print(f"found {total_images} images.")

    if total_images == 0:
        print("No images found.")
        return

    # 3. Setup CSV headers
    headers = ["Filename", "Folder_Path", "Ground_Truth_Folder", "Predicted_Dept", "Predicted_Desc", "Confidence", "Status"]
    
    # Check if we are resuming (simple logical check)
    processed_count = 0
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            processed_count = sum(1 for line in f) - 1 # Minus header
        print(f"Resuming... {processed_count} images already processed.")

    # Open files for appending
    file_mode = 'a' if processed_count > 0 else 'w'
    
    with open(OUTPUT_FILE, file_mode, newline='', encoding='utf-8') as main_csv, \
         open(LOW_CONFIDENCE_FILE, file_mode, newline='', encoding='utf-8') as low_conf_csv:
        
        writer_main = csv.DictWriter(main_csv, fieldnames=headers)
        writer_low = csv.DictWriter(low_conf_csv, fieldnames=headers)
        
        if file_mode == 'w':
            writer_main.writeheader()
            writer_low.writeheader()

        # Iterate
        print("Processing images... (Press Ctrl+C to stop safely)")
        start_time = time.time()
        
        # Skip already processed
        images_to_process = all_images[processed_count:]
        
        for idx, img_path in enumerate(tqdm(images_to_process, initial=processed_count, total=total_images)):
            try:
                # Helper for relative path
                rel_path = os.path.relpath(img_path, DATASET_ROOT)
                top_folder = rel_path.split(os.sep)[0]
                
                # --- CLASSIFY ---
                image = Image.open(img_path)
                result = classifier.classify(image)
                
                pred_dept = result['department']
                pred_conf_str = result['confidence'].replace('%', '')
                pred_conf = float(pred_conf_str)

                # --- VALIDATE ---
                # Check if predicted department is in our allowed list for this folder
                allowed_depts = FOLDER_MAP.get(top_folder, [])
                
                is_match = pred_dept in allowed_depts
                status = "MATCH" if is_match else "MISMATCH"
                
                if pred_conf < CONFIDENCE_THRESHOLD:
                    status = "LOW_CONFIDENCE"

                row = {
                    "Filename": os.path.basename(img_path),
                    "Folder_Path": rel_path,
                    "Ground_Truth_Folder": top_folder,
                    "Predicted_Dept": pred_dept,
                    "Predicted_Desc": result['description'],
                    "Confidence": result['confidence'],
                    "Status": status
                }

                # Write to Main Log
                writer_main.writerow(row)
                
                # Write to Review Log if needed
                if status == "LOW_CONFIDENCE" or status == "MISMATCH":
                    writer_low.writerow(row)
                    
                # Flush every 10 images to save progress
                if idx % 10 == 0:
                    main_csv.flush()
                    low_conf_csv.flush()

            except Exception as e:
                print(f"Error on {img_path}: {e}")

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n✅ Evaluation Complete in {duration/60:.2f} minutes.")
    print(f"📄 Full report: {OUTPUT_FILE}")
    print(f"⚠️  Review needed: {LOW_CONFIDENCE_FILE}")

if __name__ == "__main__":
    main()
