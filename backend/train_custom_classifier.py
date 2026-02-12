import os
import joblib
import torch
import numpy as np
from PIL import Image
from tqdm import tqdm
from app.classifier import CivicClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from pathlib import Path

# Config
SORTED_DATASET_ROOT = Path("sorted_dataset")
MODEL_OUTPUT_PATH = "custom_classifier_head.pkl"
EMBEDDINGS_CACHE = "embeddings_cache.pkl"

def load_data_and_extract_features(classifier):
    """
    Scans the sorted_dataset, extracts CLIP embeddings for each image,
    and returns X (features) and y (labels).
    """
    print("--- 📸 Scanning Dataset & Extracting Features ---")
    
    if os.path.exists(EMBEDDINGS_CACHE):
        print("⚡ Loading embeddings from cache...")
        data = joblib.load(EMBEDDINGS_CACHE)
        return data['X'], data['y'], data['label_map']

    X = []
    y = []
    label_map = {} # "Municipal_-_PWD_Roads" -> 0
    
    # helper to get numeric label
    def get_label_id(folder_name):
        if folder_name not in label_map:
            label_map[folder_name] = len(label_map)
        return label_map[folder_name]

    # Walk through sorted dataset
    image_paths = []
    labels_text = []
    
    for folder in os.listdir(SORTED_DATASET_ROOT):
        folder_path = SORTED_DATASET_ROOT / folder
        if folder_path.is_dir():
            for img_file in os.listdir(folder_path):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    image_paths.append(folder_path / img_file)
                    labels_text.append(folder)

    print(f"Found {len(image_paths)} images.")
    
    # Extract features in batches
    batch_size = 32
    
    with torch.no_grad():
        for i in tqdm(range(0, len(image_paths), batch_size)):
            batch_paths = image_paths[i:i+batch_size]
            batch_images = []
            valid_indices = []

            for idx, p in enumerate(batch_paths):
                try:
                    img = Image.open(p).convert("RGB")
                    # Resize for speed/memory if needed, though processor handles it
                    if img.width > 800: img.thumbnail((800,800))
                    batch_images.append(img)
                    valid_indices.append(idx) # Track which ones opened successfully
                except Exception as e:
                    print(f"Skipping {p}: {e}")

            if not batch_images:
                continue

            # Process batch
            # Note: We access the internal model/processor of the CivicClassifier instance
            inputs = classifier.processor(images=batch_images, return_tensors="pt", padding=True)
            inputs = {k: v.to(classifier.device) for k, v in inputs.items()}
            
            # Get detections from image encoder only
            image_features = classifier.model.get_image_features(**inputs)
            
            # Normalize features (important for CLIP)
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            
            # Move to CPU numpy
            features_np = image_features.cpu().numpy()
            
            # Append valid features and their corresponding labels
            for j, feat in enumerate(features_np):
                original_idx = valid_indices[j]
                X.append(feat)
                y.append(get_label_id(labels_text[i + original_idx]))

    X = np.array(X)
    y = np.array(y)
    
    print(f"Saving cache to {EMBEDDINGS_CACHE}...")
    joblib.dump({'X': X, 'y': y, 'label_map': label_map}, EMBEDDINGS_CACHE)
    
    return X, y, label_map

def train_model():
    # 1. Init CLIP wrapper (for feature extraction)
    # We use the existing class but only need the model part
    base_classifier = CivicClassifier()
    
    # 2. Get Data
    if not SORTED_DATASET_ROOT.exists():
        print(f"❌ '{SORTED_DATASET_ROOT}' not found. Run 'sort_dataset.py' first.")
        return

    X, y, label_mapping = load_data_and_extract_features(base_classifier)
    
    print(f"Features shape: {X.shape}, Labels shape: {y.shape}")
    print(f"Classes: {label_mapping}")

    # 3. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Logistic Regression (Linear Probe)
    print("--- 🧠 Training Classifier ---")
    clf = LogisticRegression(random_state=42, C=1.0, max_iter=1000, verbose=1)
    clf.fit(X_train, y_train)

    # 5. Evaluate
    print("--- 📊 Evaluation ---")
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test Set Accuracy: {acc*100:.2f}%")
    
    # Reverse mapping for report
    id_to_label = {v: k for k, v in label_mapping.items()}
    target_names = [id_to_label[i] for i in range(len(label_mapping))]
    
    print(classification_report(y_test, y_pred, target_names=target_names))

    # 6. Save
    print(f"Saving model to {MODEL_OUTPUT_PATH}...")
    
    model_data = {
        "model": clf,
        "label_map": id_to_label # Save ID->Name mapping
    }
    joblib.dump(model_data, MODEL_OUTPUT_PATH)
    print("✅ Done! You can now use this trained head in the main app.")

if __name__ == "__main__":
    train_model()
