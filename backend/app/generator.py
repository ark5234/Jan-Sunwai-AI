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
    
    TASK: Write a BRIEF formal complaint letter (maximum 150 words) to the Municipal Authority based on the image and category: '{category}'.
    
    CONTEXT:
    - Complainant: {user_name}
    - Location: {address}
    - Issue Category: {category}
    
    REQUIREMENTS:
    - Length: Maximum 3-4 short paragraphs (150 words total)
    - Tone: Formal, polite, urgent
    - Structure: 
      1. Subject Line (one line)
      2. Salutation: "To The Municipal Officer,"
      3. Issue Description: 2-3 sentences describing what you see in the image
      4. Impact: 1-2 sentences on public inconvenience
      5. Action Request: 1 sentence asking for immediate resolution
    - Be CONCISE. No elaborate descriptions. Direct and actionable.
    
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
