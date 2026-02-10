import time
import torch
import os
import random
from PIL import Image
from app.classifier import CivicClassifier
from tqdm import tqdm

DATASET_ROOT = os.path.join(os.path.dirname(__file__), "dataset")

def get_random_images(root_dir, count=50):
    image_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(dirpath, filename))
    
    if len(image_files) < count:
        return image_files
    return random.sample(image_files, count)

def main():
    print("--- 🚀 GPU vs CPU Benchmark ---")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        print(f"✅ CUDA Available: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️  CUDA NOT detected. Will run on CPU only.")

    images = get_random_images(DATASET_ROOT, 50)
    print(f"Selected {len(images)} images for testing.\n")

    # Initialize Classifier (will auto-select GPU if available based on recent change)
    # To strictly benchmark, we'd need to force CPU then GPU, but let's just see what it picked and how fast it is.
    classifier = CivicClassifier()
    print(f"Classifier Device: {classifier.device}")

    # Warmup
    print("Warming up model...")
    warmup_img = Image.new('RGB', (224, 224), color='red')
    classifier.classify(warmup_img)

    print("Starting Benchmark...")
    start_time = time.time()
    
    for img_path in tqdm(images):
        try:
            img = Image.open(img_path)
            classifier.classify(img)
        except Exception as e:
            print(f"Error: {e}")

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / len(images)

    print(f"\n--- Results ---")
    print(f"Total Time: {total_time:.4f} seconds")
    print(f"Avg Time per Image: {avg_time:.4f} seconds")
    print(f"Projected time for 23,000 images: {(avg_time * 23000) / 60:.2f} minutes")

if __name__ == "__main__":
    main()
