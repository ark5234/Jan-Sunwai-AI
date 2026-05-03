import base64
import sys
import httpx
import json

# List of models you have downloaded
MODELS = [
    "moondream:latest",
    "granite3.2-vision:2b",
    "llava-phi3:latest",
    "qwen2.5vl:3b",
]

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """You are an AI vision assistant analyzing images of civic issues. Analyze the image carefully and return ONLY valid JSON.

JSON schema:
{
  "visible_objects": ["object1", "object2", "object3"],
  "primary_issue": "short phrase describing the main problem",
  "description": "2 sentence factual description of the main objects and the environment",
  "secondary_issue": "single phrase or empty string",
  "hazards": ["hazard1"],
  "setting": "environment type",
  "confidence": "low/medium/high"
}

RULES:
- DO NOT hallucinate. ONLY describe objects that are clearly visible in the image.
- Output ONLY valid JSON matching the exact schema above.
"""

def test_models(image_path):
    print(f"\n[+] Loading image: {image_path}")
    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading image: {e}")
        return

    print("="*80)
    for model in MODELS:
        print(f"\n[*] Testing model: {model} ... (this may take a moment)")
        
        payload = {
            "model": model,
            "prompt": PROMPT,
            "images": [image_b64],
            "stream": False
        }
        
        # Moondream does not support forced JSON mode in Ollama, so we only apply it to the others
        if "moondream" not in model:
            payload["format"] = "json"
            
        try:
            with httpx.Client(timeout=240) as client:
                response = client.post(OLLAMA_URL, json=payload)
                response.raise_for_status()
                result = response.json()
                
                print(f"\n--- OUTPUT FROM {model} ---")
                try:
                    # Try to parse and pretty print JSON
                    parsed = json.loads(result['response'])
                    print(json.dumps(parsed, indent=2))
                except json.JSONDecodeError:
                    # Fallback for plain text (usually moondream)
                    print(result['response'].strip())
                    
        except httpx.ReadTimeout:
            print(f"[-] ERROR: Model {model} timed out. It might need more RAM or is loading slowly.")
        except Exception as e:
            print(f"[-] Failed to get response from {model}: {e}")
            
        print("\n" + "="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_vision_models.py <path_to_image>")
        sys.exit(1)
    
    test_models(sys.argv[1])
