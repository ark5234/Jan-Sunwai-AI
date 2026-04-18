import contextlib
from contextlib import asynccontextmanager
from typing import Any, cast
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
from app.routers import complaints, users, health, triage, notifications, analytics, public, workers
from app.database import connect_to_mongo, close_mongo_connection
from app.services.llm_queue import llm_queue_service
from app.services.escalation import escalation_loop
from app.config import settings
from app.rate_limiter import (
    limiter,
    RATE_LIMITING_AVAILABLE,
    RateLimitExceeded,
    SlowAPIMiddleware,
    _rate_limit_exceeded_handler,
)
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "uploads"

# --- 1. Global Logging Setup ---
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JanSunwaiAI")

file_handler = RotatingFileHandler(str(LOGS_DIR / "app.log"), maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# H-02 / P3-B: Store the escalation task so it can be cancelled on clean shutdown.
_escalation_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _escalation_task

    logger.info("Starting up application...")

    # Validate JWT secret strength before accepting traffic in production
    if settings.is_production:
        _WEAK_PATTERNS = ("change-me", "secret", "default", "changethis", "jwt_secret", "your-super")
        secret = settings.jwt_secret_key
        if len(secret) < 32 or any(p in secret.lower() for p in _WEAK_PATTERNS):
            raise RuntimeError(
                "JWT_SECRET_KEY is too weak or is a placeholder. "
                "Generate a secure key: python -c \"import secrets; print(secrets.token_hex(64))\""
            )
        if not settings.enable_rate_limiting:
            raise RuntimeError("RATE_LIMIT_ENABLED must be true in production")
        if not RATE_LIMITING_AVAILABLE:
            raise RuntimeError(
                "Rate limiting is required in production but slowapi is unavailable. "
                "Install slowapi and restart."
            )

    await connect_to_mongo()
    await llm_queue_service.start()

    # H-02 / P3-B: Save handle so we can cancel on shutdown
    _escalation_task = asyncio.create_task(escalation_loop())
    logger.info("Escalation background loop started.")

    yield  # ← app runs here

    # Shutdown
    logger.info("Shutting down application...")

    if _escalation_task is not None:
        _escalation_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _escalation_task
        logger.info("Escalation loop stopped cleanly.")

    await llm_queue_service.stop()
    await close_mongo_connection()


app = FastAPI(title="Jan-Sunwai AI API", version="1.0.0", lifespan=lifespan)

if RATE_LIMITING_AVAILABLE and SlowAPIMiddleware is not None and _rate_limit_exceeded_handler is not None:
    app.state.limiter = limiter
    app.add_exception_handler(
        cast(type[Exception], RateLimitExceeded),
        cast(Any, _rate_limit_exceeded_handler),
    )
    app.add_middleware(SlowAPIMiddleware)
    logger.info("Rate limiting middleware enabled")
else:
    logger.info("Rate limiting middleware disabled (missing slowapi or RATE_LIMIT_ENABLED=false)")

# --- 2. CORS Middleware — MUST be registered first so its headers appear on
#        ALL responses including error/exception responses. If added after other
#        middleware or exception handlers, error responses bypass CORS injection.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Performance Profiling Middleware ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.4f}s")

    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    img_connect_sources = "https:" if settings.is_production else "https: http:"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"img-src 'self' data: blob: {img_connect_sources}; "
        f"connect-src 'self' {img_connect_sources}; "
        # BL-05: 'unsafe-inline' kept for now — nonce-based CSP is a Phase 4 item
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "frame-ancestors 'none'"
    )
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# --- 4. Global Exception Handler ---
# NOTE: FastAPI exception handlers bypass CORSMiddleware, so CORS headers are
# injected manually here or the browser reports a CORS error instead of the real error.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # P1-D: Log full details server-side, NEVER send str(exc) to the client in production.
    logger.error("Unhandled Exception: %s", str(exc), exc_info=True)

    origin = request.headers.get("origin", "")
    cors_headers = {}
    if origin and (origin in settings.allowed_origins or "*" in settings.allowed_origins):
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"

    # P1-D: Only expose exception details in non-production environments.
    content: dict = {"message": "Internal Server Error"}
    if not settings.is_production:
        content["details"] = str(exc)

    return JSONResponse(
        status_code=500,
        content=content,
        headers=cors_headers,
    )


# Mount Uploads for Static Access
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ---------------------------------------------------------------------------
# H-01 / P4-A: Canonical versioned routes (/api/v1/...).
# Unversioned routes preserved via deprecated=True for 3-month backwards-compat
# window. Clients should migrate to /api/v1/* prefix.
# Removal target: 2026-07-17
# ---------------------------------------------------------------------------

# Primary versioned routes
app.include_router(complaints.router, prefix="/api/v1", tags=["Complaints v1"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users v1"])
app.include_router(health.router, prefix="/api/v1", tags=["Health v1"])
app.include_router(triage.router, prefix="/api/v1", tags=["Triage v1"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications v1"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics v1"])
app.include_router(public.router, prefix="/api/v1", tags=["Public v1"])
app.include_router(workers.router, prefix="/api/v1", tags=["Workers v1"])


@app.get("/")
def read_root():
    return {
        "message": "Jan-Sunwai AI Backend Online",
        "api_version": "v1",
        "docs": "/docs",
        "canonical_prefix": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
