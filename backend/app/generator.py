import io
import ollama
import os
from PIL import Image
from app.config import settings


def _load_image_as_jpeg_bytes(image_path: str) -> bytes:
    """Convert any image to RGB JPEG bytes to avoid GGML_ASSERT/format errors."""
    with Image.open(image_path) as img:
        if img.mode not in ("RGB",):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()


def generate_complaint(image_path, classification_result, user_details, location_details):
    """
    Generates a formal government complaint letter using the configured Ollama vision model.
    
    Args:
        image_path (str): Path to the image file.
        classification_result (dict): Result from the classifier (label, confidence).
        user_details (dict): User info (name).
        location_details (dict): Location info (address, lat/long).
    """
    
    # Validation
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}."

    # Use the civic department/category, not 'label' which is the raw vision description text
    category = classification_result.get("department") or classification_result.get("label", "Civic Issue")
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
        # Use explicit client so host URL comes from config (not localhost default)
        client = ollama.Client(host=settings.ollama_base_url)
        image_bytes = _load_image_as_jpeg_bytes(image_path)

        # Try primary vision model; fall back to lighter model on OOM
        models_to_try = [settings.vision_model]
        if settings.fallback_vision_model and settings.fallback_vision_model != settings.vision_model:
            models_to_try.append(settings.fallback_vision_model)

        response = None
        used_model = settings.vision_model
        for model_name in models_to_try:
            try:
                response = client.generate(
                    model=model_name,
                    prompt=prompt,
                    images=[image_bytes]
                )
                used_model = model_name
                break
            except Exception as model_err:
                err_msg = str(model_err).lower()
                is_oom = any(kw in err_msg for kw in [
                    "memory", "oom", "out of memory", "not enough",
                    "insufficient", "cannot allocate",
                ])
                if is_oom and model_name != models_to_try[-1]:
                    print(f"[generator] {model_name} OOM, falling back to {models_to_try[-1]}")
                    try:
                        client.generate(model=model_name, prompt="", keep_alive=0)
                    except Exception:
                        pass
                    continue
                raise

        # Unload vision model after letter generation to free VRAM
        try:
            client.generate(model=used_model, prompt="", keep_alive=0)
        except Exception:
            pass
        return response['response']
    except Exception as e:
        return f"System Note: Automated drafting failed ({str(e)}). Please draft manually based on category: {category}."
