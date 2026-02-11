import ollama
import os

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
    You are a professional assistant for drafting formal government complaints in India.
    
    TASK: Write a formal complaint letter to the relevant Municipal Authority based on the provided image and the verified category: '{category}'.
    
    CONTEXT:
    - Complainant: {user_name}
    - Location: {address}
    - Issue Category: {category}
    
    REQUIREMENTS:
    - Tone: Strictly formal, polite, and urgent.
    - Structure: 
      1. Subject Line: Precise and includes the location.
      2. Salutation: "To The Municipal Officer,"
      3. Body: Describe the visual evidence from the image professionally. Explain the public inconvenience caused.
      4. Location Mention: Explicitly state the location.
      5. Closing: Request immediate action.
    - Do NOT use flowery language. Be direct.
    
    Write ONLY the letter content. No preamble.
    """
    
    try:
        # Call Ollama
        response = ollama.generate(
            model='llava', 
            prompt=prompt, 
            images=[image_path] 
        )
        return response['response']
    except Exception as e:
        return f"System Note: Automated drafting failed ({str(e)}). Please draft manually based on category: {category}."
