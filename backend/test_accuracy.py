import os
import random
import glob
from PIL import Image
from app.classifier import CivicClassifier
from typing import List, Dict

DATASET_ROOT = os.path.join(os.path.dirname(__file__), "dataset")

def get_all_images(root_dir: str) -> List[str]:
    """Recursively find all .jpg and .png images in the dataset folder."""
    image_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(dirpath, filename))
    return image_files

def main():
    print("--- 🔍 Model Accuracy Test ---")
    
    # 1. Setup
    if not os.path.exists(DATASET_ROOT):
        print(f"❌ Dataset not found at: {DATASET_ROOT}")
        print("Please place your 'dataset' folder in the 'backend' directory.")
        return

    print("Scanning dataset...", end="")
    images = get_all_images(DATASET_ROOT)
    print(f" Found {len(images)} images.")

    if len(images) == 0:
        print("No images found to test.")
        return

    # 2. Select Test Set
    sample_size = min(50, len(images))
    test_set = random.sample(images, sample_size)
    print(f"Testing on {sample_size} random images...\n")

    # 3. Initialize Model
    try:
        classifier = CivicClassifier()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # 4. Run Inference
    results = []
    for i, img_path in enumerate(test_set):
        try:
            filename = os.path.basename(img_path)
            # Try to infer 'Ground Truth' department from folder path (heuristic)
            # Path ex: dataset/Air_Pollution/pothole.jpg -> 'Air_Pollution'
            # Path ex: dataset/Civil_Dept/Roads/img.jpg -> 'Civil_Dept'
            # This is rough, as folder names don't exactly match our "Civil Dept" strings, 
            # but it helps human review.
            folder_path = os.path.dirname(img_path)
            parent_folder = os.path.basename(folder_path) # e.g., 'Air_Pollution-_Pothole'
            
            # Go up one level to see if it's the main Category folder
            grandparent_folder = os.path.basename(os.path.dirname(folder_path)) # e.g., 'Air_Pollution'
            
            ground_truth_hint = f"{grandparent_folder}/{parent_folder}"

            image = Image.open(img_path)
            prediction = classifier.classify(image)
            
            print(f"[{i+1}/{sample_size}] {filename}")
            print(f"   📂 Source: {ground_truth_hint}")
            print(f"   🤖 Pred:   {prediction['department']} ({prediction.get('label', prediction.get('description', 'Unknown'))})")
            print(f"   📊 Conf:   {prediction['confidence']}")
            print("-" * 40)
            
            results.append({
                "file": filename,
                "source": ground_truth_hint,
                "prediction": prediction
            })
            
        except Exception as e:
            print(f"❌ Error processing {img_path}: {e}")

    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()
