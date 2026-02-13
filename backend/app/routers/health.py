from fastapi import APIRouter
import ollama

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
