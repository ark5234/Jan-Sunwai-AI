"""
download_models.py — Pull the Ollama models configured in .env (or defaults).

Usage:
    python backend/download_models.py

Model names are read from:
    VISION_MODEL    (default: qwen2.5vl:3b)
    REASONING_MODEL (default: llama3.2:1b)

To change models: edit backend/.env then re-run this script.
"""
import subprocess
import sys
from pathlib import Path

# Make sure app/ is importable when called from project root
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings


def pull(model: str) -> None:
    print(f"  Pulling {model} ...")
    result = subprocess.run(["ollama", "pull", model])
    if result.returncode == 0:
        print(f"  ✅ {model} ready")
    else:
        print(f"  ❌ Failed to pull {model} (exit code {result.returncode})")
        sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ 'ollama' not found in PATH. Install Ollama first: https://ollama.com/download")
        sys.exit(1)

    print("Pulling Ollama models configured in .env...")
    print(f"  Vision model    : {settings.vision_model}")
    print(f"  Reasoning model : {settings.reasoning_model}")
    print()

    pull(settings.vision_model)
    pull(settings.reasoning_model)

    print()
    print("✅ All models ready.")
    print("  To use different models: edit VISION_MODEL / REASONING_MODEL in backend/.env")
    print("  then re-run: python backend/download_models.py")
