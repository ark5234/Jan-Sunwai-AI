from fastapi import APIRouter
import ollama
import requests

from app.config import settings
from app.database import get_database


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def live_check():
    return {"status": "ok"}


@router.get("/ready")
async def ready_check():
    db_ok = True
    db_error = None
    try:
        db = get_database()
        await db.command("ping")
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    return {
        "status": "ready" if db_ok else "degraded",
        "database": {"ok": db_ok, "error": db_error},
    }


@router.get("/models")
async def model_health():
    ollama_ok = True
    ollama_error = None
    models = []
    try:
        response = ollama.list()
        models = response.get("models", []) if isinstance(response, dict) else []
    except Exception as exc:
        ollama_ok = False
        ollama_error = str(exc)

    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": {
            "ok": ollama_ok,
            "error": ollama_error,
            "models": models,
        },
    }


@router.get("/gpu")
async def gpu_check():
    """
    Asks Ollama which models are currently loaded and whether they are
    using VRAM (GPU) or RAM (CPU).
    A model with size_vram > 0 is running on GPU.
    """
    try:
        resp = requests.get("http://localhost:11434/api/ps", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        running_models = data.get("models", [])

        gpu_active = any(
            m.get("size_vram", 0) > 0 for m in running_models
        )

        return {
            "gpu_active": gpu_active,
            "note": "gpu_active=true means at least one model is loaded in VRAM",
            "configured_models": {
                "vision": settings.vision_model,
                "reasoning": settings.reasoning_model,
            },
            "running_models": [
                {
                    "name": m.get("name"),
                    "size_mb": round(m.get("size", 0) / 1_048_576),
                    "vram_mb": round(m.get("size_vram", 0) / 1_048_576),
                    "on_gpu": m.get("size_vram", 0) > 0,
                }
                for m in running_models
            ],
        }
    except Exception as exc:
        return {
            "gpu_active": False,
            "error": str(exc),
            "note": "Ollama may not be running, or no model is currently loaded.",
        }
