from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

class CivicClassifier:
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
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
        # Ensure image is in RGB mode (CLIP expects RGB)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        inputs = self.processor(text=self.labels, images=image, return_tensors="pt", padding=True) # type: ignore
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        
        # Get the highest probability
        confidence, index = torch.max(probs, 1)
        # Cast to int to satisfy type checker (though item() on index tensor is already int-like)
        predicted_label = self.labels[int(index.item())]
        
        return {
            "department": self.label_map[predicted_label],
            "description": predicted_label,
            "confidence": f"{confidence.item() * 100:.2f}%"
        }
