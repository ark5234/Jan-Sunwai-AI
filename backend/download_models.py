import subprocess
from typing import Iterable


def pull_ollama_models(models: Iterable[str]):
    """
    Pulls Ollama models by calling `ollama pull <model>` for each one.
    Replaces the old CLIP download — no HuggingFace, no torch required.
    """
    for model in models:
        print(f"Pulling {model} ...")
        result = subprocess.run(["ollama", "pull", model], capture_output=False)
        if result.returncode == 0:
            print(f"✅ {model} ready")
        else:
            print(f"❌ Failed to pull {model}")


def download_ollama_models(models: Iterable[str]):
    for model in models:
        print(f"Starting Ollama pull for: {model}")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"✅ Pulled {model}")
        except FileNotFoundError:
            print("❌ 'ollama' CLI not found. Install Ollama and ensure it is in PATH.")
            return
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to pull {model}: {e}")


def download_all_models():
    download_clip_model()
    download_ollama_models([
        "qwen2.5vl:3b",
        "llama3.2:1b",
        "llava",
    ])
    print("✅ Model setup completed")

if __name__ == "__main__":
    download_all_models()
