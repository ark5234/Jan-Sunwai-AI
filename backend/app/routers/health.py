import asyncio
import requests
from fastapi import APIRouter
from app.config import settings
from app.database import get_database
import logging

logger = logging.getLogger("JanSunwaiAI.health")

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def live_check():
    return {"status": "ok"}


@router.get("/ready")
async def ready_check():
    """
    P3-E: Returns only boolean DB status — never exposes raw exception text.
    DB error is logged server-side for operators.
    """
    db_ok = True
    try:
        db = get_database()
        await db.command("ping")
    except Exception as exc:
        db_ok = False
        logger.warning("DB readiness check failed: %s", exc)  # server log only

    return {
        "status": "ready" if db_ok else "degraded",
        "database": {"ok": db_ok},
        # P3-E: error string removed from response — was leaking DB topology/credentials
    }


@router.get("/models")
async def model_health():
    """P3-C: Ollama SDK call wrapped in asyncio.to_thread — no longer blocks event loop."""
    import ollama

    ollama_ok = True
    models = []
    try:
        client = ollama.Client(host=settings.ollama_base_url)
        # P3-C: was a blocking sync call inside async handler — fixed with to_thread
        response = await asyncio.to_thread(client.list)
        # Ollama SDK can return ListResponse (models attribute) or dict payloads.
        raw_models = []
        if hasattr(response, "models"):
            raw_models = list(getattr(response, "models") or [])
        elif isinstance(response, dict):
            raw_models = list(response.get("models", []) or [])

        normalized: list[str] = []
        for item in raw_models:
            if isinstance(item, dict):
                name = item.get("model") or item.get("name")
            else:
                name = getattr(item, "model", None) or getattr(item, "name", None)
            if name:
                normalized.append(str(name))

        models = normalized
    except Exception as exc:
        ollama_ok = False
        logger.warning("Model health check failed: %s", exc)

    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": {
            "ok": ollama_ok,
            "error": None if ollama_ok else "unavailable",
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
        resp = await asyncio.to_thread(
            requests.get,
            f"{settings.ollama_base_url}/api/ps",
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        running_models = data.get("models", [])

        gpu_active = any(
            m.get("size_vram", 0) > 0 for m in running_models
        )

        return {
            "gpu_active": gpu_active,
            "note": (
                "gpu_active=true means at least one model is currently loaded in VRAM. "
                "During analysis, the vision model runs first then is UNLOADED to free VRAM "
                "before the reasoning model loads — so you may see only the reasoning model here "
                "if checked mid-pipeline or after analysis completes."
            ),
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
        logger.warning("GPU health check failed: %s", exc)
        return {
            "gpu_active": False,
            "error": "unavailable",
            "note": "Ollama may not be running, or no model is currently loaded.",
        }
