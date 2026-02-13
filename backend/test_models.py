import argparse
import sys
import os
from PIL import Image
from app.classifier import CivicClassifier
from app.generator import generate_complaint
from app.geotagging import extract_location

def main():
    parser = argparse.ArgumentParser(description="Test Jan-Sunwai AI Models")
    parser.add_argument("image_path", help="Path to the image file to analyze")
    parser.add_argument("--skip-llm", action="store_true", help="Skip the LLaVA complaint generation (faster)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: File not found at {args.image_path}")
        return

    print(f"Loading image: {args.image_path}...")
    try:
        image = Image.open(args.image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # 1. Test Classifier
    print("\n--- Testing CLIP Classifier ---")
    result = None
    try:
        classifier = CivicClassifier()
        print("Model loaded. Classifying...")
        result = classifier.classify(image)
        print("\nClassification Result:")
        print(f"Department: {result['department']}")
        print(f"Description: {result.get('label', 'N/A')}")
        print(f"Confidence: {result['confidence']}")
    except Exception as e:
        print(f"Error during classification: {e}")

    # 2. Test Geotagging
    print("\n--- Testing Geotagging ---")
    location = None
    try:
        location = extract_location(image)
        print("\nLocation Result:")
        if location:
            print(f"Address: {location.get('address')}")
            print(f"Coordinates: {location.get('coordinates')}")
            if location.get('error'):
                print(f"Note: {location.get('error')}")
        else:
            print("No location data found.")
    except Exception as e:
        print(f"Error during geotagging: {e}")

    # 3. Test LLaVA Generator
    if result and not args.skip_llm:
        print("\n--- Testing LLaVA Complaint Generation ---")
        print("(Ensure 'ollama serve' is running and you have pulled 'llava')")
        try:
            # Re-read raw bytes for the generator
            with open(args.image_path, "rb") as f:
                image_bytes = f.read()
            
            user_details = {"name": "Test User"}
            loc_details = location if location else {"address": "Unknown Location"}
            classification_result = {"label": result['department'], "confidence": 0.9} # Mock mapping
            
            print("Generating complaint...")
            # Updated signature: image_path, classification_result, user_details, location_details
            # Note: generate_complaint in generator.py now likely expects a path, not bytes, based on my earlier edits?
            # Let's check generator.py one more second to be sure.
            
            complaint = generate_complaint(args.image_path, classification_result, user_details, loc_details)
            print("\nGenerated Complaint:")
            print("-" * 40)
            print(complaint)
            print("-" * 40)
        except Exception as e:
            print(f"Error during generation: {e}")

if __name__ == "__main__":
    main()
