import ollama
import os
from app.config import settings

def generate_complaint(image_path, classification_result, user_details, location_details):
    """
    Generates a formal government complaint letter using LLaVA.
    
    Args:
        image_path (str): Path to the image file.
        classification_result (dict): Result from the classifier (label, confidence).
        user_details (dict): User info (name).
        location_details (dict): Location info (address, lat/long).
    """
    
    # Validation
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}."

    category = classification_result.get("label", "Civic Issue")
    user_name = user_details.get("name", "Concerned Citizen")
    address = location_details.get("address", "New Delhi (Exact location pending)")
    
    prompt = f"""
    You are writing a civic grievance complaint for Indian municipal authorities.
    
    TASK: Write a SHORT grievance complaint (80-100 words) about the issue shown in the image.
    
    DETAILS:
    - Complainant: {user_name}
    - Location: {address}
    - Issue Type: {category}
    
    FORMAT:
    Subject: [One line describing the issue]
    
    To The Municipal Officer,
    
    [2-3 sentences describing what you observe in the image and why it's a problem]
    
    [1 sentence on how it affects public convenience/safety]
    
    [1 sentence requesting immediate action]
    
    Respectfully submitted,
    {user_name}
    
    TONE: Direct, concise, factual. Like filing a grievance, not writing a formal letter.
    NO elaborate descriptions. Maximum 100 words total.
    """
    
    try:
        # Call Ollama — reuse vision model (qwen2.5-vl) which is already warm in memory
        response = ollama.generate(
            model=settings.vision_model,
            prompt=prompt,
            images=[image_path]
        )
        return response['response']
    except Exception as e:
        return f"System Note: Automated drafting failed ({str(e)}). Please draft manually based on category: {category}."
