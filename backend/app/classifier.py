from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

class CivicClassifier:
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.labels = [
            "A photo of a broken road or pavement", 
            "A photo of stagnant water or mosquito breeding", 
            "A photo of smoke or air pollution", 
            "A photo of garbage or dead animals", 
            "A photo of broken street light",
            "A photo of construction dust",
            "A photo of water logging"
        ]
        self.label_map = {
            "A photo of a broken road or pavement": "Civil Dept",
            "A photo of stagnant water or mosquito breeding": "VBD Dept",
            "A photo of smoke or air pollution": "Pollution Control",
            "A photo of garbage or dead animals": "Public Health",
            "A photo of broken street light": "Electricity Dept",
            "A photo of construction dust": "Pollution Control",
            "A photo of water logging": "Drainage Dept"
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
