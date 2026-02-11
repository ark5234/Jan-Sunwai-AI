from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

class CivicClassifier:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Loading CLIP on device: {self.device}")
        
        # We explicitly cast self.device to str to satisfy Pylance/Type Checker if needed, 
        # though .to() accepts standard device strings.
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.model.to(self.device) # type: ignore
        
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.labels = [
            # Civil / Road Issues
            "A photo of a broken road or pothole",
            "A photo of damaged pavement or footpath",
            "A photo of construction material dumped on road",
            
            # Drainage / Monsoon Issues
            "A photo of water logging or flooded street",
            "A photo of a blocked drain or sewer",
            "A photo of stagnant water",

            # Garbage / Sanitation
            "A photo of a garbage dump",
            "A photo of overflowing trash bin",
            "A photo of dead animal on street",
            
            # Electrical
            "A photo of a broken street light",
            "A photo of dangling electrical wires",
            "A photo of an open transformer",

            # Horticulture / Parks
            "A photo of a fallen tree",
            "A photo of unmaintained park or dry plants",

            # Pollution
            "A photo of air pollution or thick smoke",
            "A photo of burning garbage",

            # Encroachment (Enforcement)
            "A photo of illegal shop or encroachment on footpath",
            "A photo of unauthorized construction"
        ]
        self.label_map = {
            # Civil
            "A photo of a broken road or pothole": "Civil Engineering Dept",
            "A photo of damaged pavement or footpath": "Civil Engineering Dept",
            "A photo of construction material dumped on road": "Civil Engineering Dept",
            
            # Drainage
            "A photo of water logging or flooded street": "Drainage Dept",
            "A photo of a blocked drain or sewer": "Drainage Dept",
            "A photo of stagnant water": "Drainage Dept", # Can also be VBD (Health)

            # Sanitation
            "A photo of a garbage dump": "Sanitation Dept",
            "A photo of overflowing trash bin": "Sanitation Dept",
            "A photo of dead animal on street": "Public Health Dept",

            # Electrical
            "A photo of a broken street light": "Electricity Dept",
            "A photo of dangling electrical wires": "Electricity Dept",
            "A photo of an open transformer": "Electricity Dept",

            # Horticulture
            "A photo of a fallen tree": "Horticulture Dept",
            "A photo of unmaintained park or dry plants": "Horticulture Dept",

            # Pollution
            "A photo of air pollution or thick smoke": "Pollution Control Dept",
            "A photo of burning garbage": "Pollution Control Dept",

            # Enforcement
            "A photo of illegal shop or encroachment on footpath": "Enforcement Dept",
            "A photo of unauthorized construction": "Enforcement Dept"
        }

    def classify(self, image: Image.Image):
        try:
            # 1. Image Preprocessing
            # Convert to RGB (standard for CLIP)
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Resize if the image is excessively large (> 1600px) to optimization inference speed
            # CLIP usually resizes to 224x224, so sending 4k images is wasteful.
            max_size = 1600
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size))

            # 2. Model Inference
            inputs = self.processor(text=self.labels, images=image, return_tensors="pt", padding=True) # type: ignore
            
            # Move inputs to the same device as the model (GPU/CPU)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            
            # 3. Result Parsing
            confidence, index = torch.max(probs, 1)
            predicted_label = self.labels[int(index.item())]
            
            return {
                "department": self.label_map[predicted_label],
                "label": predicted_label,
                "confidence": float(confidence.item())
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

