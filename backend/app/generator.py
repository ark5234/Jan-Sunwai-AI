import ollama
from PIL import Image
import io

def generate_complaint(image_bytes, user_details, location_details):
    # This assumes the user has Ollama running with llava model pulled
    # 'ollama pull llava'
    
    prompt = f"""
    You are an AI assistant for a civic grievance redressal system. 
    Analyze the provided image which shows a civic issue (like garbage, broken road, waterlogging, etc.).
    
    Write a formal complaint letter to the Municipal Officer.
    
    User Name: {user_details.get('name', 'Concerned Citizen')}
    Location: {location_details.get('address', 'Unknown Location')}
    
    The letter should be professional, concise, and state the urgency.
    Subject line should be clear.
    Structure:
    Subject: [Subject]
    Dear Municipal Officer,
    [Body describing the issue based on image]
    [Mention urgency and safety risk if apparent]
    Please resolve this at the earliest.
    
    Regards,
    {user_details.get('name', 'Concerned Citizen')}
    """
    
    try:
        response = ollama.generate(model='llava', prompt=prompt, images=[image_bytes])
        return response['response']
    except Exception as e:
        return f"Error generating complaint: {str(e)}. Ensure Ollama is running with 'llava' model."
