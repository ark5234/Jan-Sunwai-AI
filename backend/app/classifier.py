from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import os
import joblib
import numpy as np

class CivicClassifier:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Loading CLIP on device: {self.device}")
        
        # We explicitly cast self.device to str to satisfy Pylance/Type Checker if needed, 
        # though .to() accepts standard device strings.
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.model.to(self.device) # type: ignore
        
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Check for Custom Trained Head
        self.custom_head = None
        self.custom_labels = None
        custom_head_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "custom_classifier_head.pkl")
        
        if os.path.exists(custom_head_path):
            try:
                print(f"🧠 Loading Custom Classifier Head from {custom_head_path}...")
                data = joblib.load(custom_head_path)
                self.custom_head = data['model']
                self.custom_labels = data['label_map']
                print("✅ Custom Classifier Loaded!")
            except Exception as e:
                print(f"⚠️ Failed to load custom classifier: {e}")
        
        self.labels = [
            # 1. Local Municipal Authorities (Urban Centers)
            # PWD / Civil Engineering
            "A photo of a broken road or pothole",
            "A photo of damaged pavement or footpath",
            "A photo of bridge damage",
            
            # Sanitation & Solid Waste Management
            "A photo of a garbage dump or pile",
            "A photo of overflowing trash bin",
            "A photo of a dirty public toilet",

            # Horticulture
            "A photo of a fallen tree",
            "A photo of unmaintained park or dry plants",

            # Street Lighting (Electrical)
            "A photo of a broken street light",
            "A photo of a non-functional street lamp",

            # Water Supply & Sewerage
            "A photo of water logging or flooded street",
            "A photo of a blocked drain or sewer",
            "A photo of a water pipe leak",

            # 2. Specialized Utility & State Service Providers
            # Power Distribution (DISCOMs)
            "A photo of dangling electrical wires",
            "A photo of an open transformer",
            "A photo of hazardous hanging power cables",

            # State Transport
            "A photo of a damaged bus shelter or terminal",
            "A photo of a broken state bus",

            # Pollution Control Boards
            "A photo of air pollution or thick smoke",
            "A photo of industrial waste dumping",
            "A photo of burning garbage",

            # 3. Safety & Law Enforcement
            # Local Police
            "A photo of illegal parking",
            "A photo of encroachment on footpath", # Also shared with Municipal/Enforcement
            "A photo of a public nuisance or brawl",
            
            # Traffic Police
            "A photo of traffic signal failure",
            "A photo of traffic congestion or obstruction"
        ]
        
        # Labels for non-civic images to filter out irrelevant photos
        self.negative_labels = [
            "A photo of a person or selfie",
            "A photo of a group of people",
            "A photo of an anime character or cartoon",
            "A photo of a gaming screen or screenshot",
            "A photo of food or restaurant meal",
            "A photo of indoor furniture or appliance",
            "A photo of a document or paper",
            "A photo of a blurry or unclear object",
            "A photo of an animal or pet",
            "A photo of a clear blue sky",
            "A photo of a beautiful landscape or nature"
        ]
        
        self.label_map = {
            # 1. Local Municipal Authorities
            # PWD
            "A photo of a broken road or pothole": "Municipal - PWD (Roads)",
            "A photo of damaged pavement or footpath": "Municipal - PWD (Roads)",
            "A photo of bridge damage": "Municipal - PWD (Bridges)",
            
            # Sanitation
            "A photo of a garbage dump or pile": "Municipal - Sanitation",
            "A photo of overflowing trash bin": "Municipal - Sanitation",
            "A photo of a dirty public toilet": "Municipal - Sanitation",

            # Horticulture
            "A photo of a fallen tree": "Municipal - Horticulture",
            "A photo of unmaintained park or dry plants": "Municipal - Horticulture",

            # Street Lighting
            "A photo of a broken street light": "Municipal - Street Lighting",
            "A photo of a non-functional street lamp": "Municipal - Street Lighting",

            # Water & Sewerage
            "A photo of water logging or flooded street": "Municipal - Water & Sewerage",
            "A photo of a blocked drain or sewer": "Municipal - Water & Sewerage",
            "A photo of a water pipe leak": "Municipal - Water & Sewerage",

            # 2. Specialized Utility
            # DISCOMs
            "A photo of dangling electrical wires": "Utility - Power (DISCOM)",
            "A photo of an open transformer": "Utility - Power (DISCOM)",
            "A photo of hazardous hanging power cables": "Utility - Power (DISCOM)",

            # Transport
            "A photo of a damaged bus shelter or terminal": "State Transport",
            "A photo of a broken state bus": "State Transport",

            # Pollution
            "A photo of air pollution or thick smoke": "Pollution Control Board",
            "A photo of industrial waste dumping": "Pollution Control Board",
            "A photo of burning garbage": "Pollution Control Board",

            # 3. Safety & Law Enforcement
            # Local Police
            "A photo of illegal parking": "Police - Local Law Enforcement",
            "A photo of encroachment on footpath": "Police - Local Law Enforcement",
            "A photo of a public nuisance or brawl": "Police - Local Law Enforcement",
            
            # Traffic Police
            "A photo of traffic signal failure": "Police - Traffic",
            "A photo of traffic congestion or obstruction": "Police - Traffic"
        }

    def classify(self, image: Image.Image):
        try:
            # 1. Image Preprocessing
            # Convert to RGB (standard for CLIP)
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize
            max_size = 1600
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size))

            # --- CUSTOM HEAD PATH (If Trained) ---
            if self.custom_head and self.custom_labels:
                # Get embeddings only
                inputs = self.processor(images=image, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    image_features = self.model.get_image_features(**inputs)
                
                # Normalize
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                
                # Predict
                features_np = image_features.cpu().numpy()
                probs = self.custom_head.predict_proba(features_np)[0]
                pred_idx = np.argmax(probs)
                confidence_val = float(probs[pred_idx])
                
                predicted_category_name = self.custom_labels[pred_idx]
                
                # Map back to our standard format
                # The custom model predicts "Municipal_-_PWD_Roads" (Folder Name)
                # We need to clean it up for the frontend
                
                # Simple cleanup: Replace underscores with spaces
                clean_label = predicted_category_name.replace("_", " ").replace("And", "&")
                
                # Determine department from the category name itself (it's embedded)
                # Ex: "Municipal_-_Sanitation" -> Department: "Sanitation" or "Municipal - Sanitation"
                
                return {
                    "department": clean_label, # Use the specific trained category as the department key
                    "label": f"Highly confident assessment: {clean_label}",
                    "confidence": confidence_val,
                    "is_valid": True # We assume trained model output is valid if confident
                }

            # --- ZERO SHOT FALLBACK (Legacy) ---
            # 2. Model Inference
            # Combine legitimate labels with negative labels for "Open Set" classification simulation
            all_labels = self.labels + self.negative_labels
            
            inputs = self.processor(text=all_labels, images=image, return_tensors="pt", padding=True) # type: ignore
            
            # Move inputs to the same device as the model (GPU/CPU)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            
            # 3. Result Parsing
            confidence, index = torch.max(probs, 1)
            index_val = int(index.item())
            confidence_val = float(confidence.item())
            
            predicted_label = all_labels[index_val]
            
            # Logic to reject irrelevant images
            if predicted_label in self.negative_labels:
                return {
                    "department": "Invalid Content",
                    "label": "Not a civic issue (Detected: " + predicted_label.replace("A photo of ", "") + ")",
                    "confidence": confidence_val,
                    "is_valid": False
                }
            
            # Logic to reject low confidence predictions (Threshold: 50%)
            if confidence_val < 0.5:
                 return {
                    "department": "Uncertain",
                    "label": "Low confidence prediction (Possibly: " + predicted_label.replace("A photo of ", "") + ")",
                    "confidence": confidence_val,
                    "is_valid": False
                }

            return {
                "department": self.label_map.get(predicted_label, "General"),
                "label": predicted_label,
                "confidence": confidence_val,
                "is_valid": True
            }
        except Exception as e:
            # In case of any processing error, return a generic failure rather than crashing
            print(f"Classification Error: {str(e)}")
            return {
                "department": "Unknown",
                "label": "Could not classify image",
                "confidence": 0.0,
                "error": str(e)
            }

