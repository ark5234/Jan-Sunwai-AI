import os
from transformers import CLIPProcessor, CLIPModel

def download_clip_model():
    """
    Downloads and caches the OpenAI CLIP model locally.
    This ensures that the application doesn't need to download the model during runtime/startup.
    The models are stored in the default Hugging Face cache directory.
    """
    model_name = "openai/clip-vit-base-patch32"
    print(f"Starting download for: {model_name}")
    print("This may take a few minutes depending on your internet connection...")

    try:
        # Downloading Model and Processor
        # verify=True ensures SSL certificates are valid
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        
        print(f"✅ Successfully downloaded and cached '{model_name}'")
        print(f"Cache location: {os.path.expanduser('~/.cache/huggingface/hub')}")
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")

if __name__ == "__main__":
    download_clip_model()
