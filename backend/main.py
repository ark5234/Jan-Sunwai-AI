from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import complaints, users, health, triage
from app.database import connect_to_mongo, close_mongo_connection
from app.services.llm_queue import llm_queue_service
from app.config import settings
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "uploads"

# --- 1. Global Logging Setup ---
# Create logs directory
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JanSunwaiAI")

# File Handler (Rotate after 5MB, keep 3 backups)
file_handler = RotatingFileHandler(str(LOGS_DIR / "app.log"), maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    logger.info("Starting up application...")
    await connect_to_mongo()
    await llm_queue_service.start()
    yield
    # Shutdown: Close DB connection
    logger.info("Shutting down application...")
    await llm_queue_service.stop()
    await close_mongo_connection()

app = FastAPI(title="Jan-Sunwai AI API", version="1.0.0", lifespan=lifespan)

# --- 2. Performance Profiling Middleware ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log slow requests (> 1 second)
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.4f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads for Static Access
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Include Routers
app.include_router(complaints.router, tags=["Complaints"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(health.router)
app.include_router(triage.router)

@app.get("/")
def read_root():
    return {"message": "Jan-Sunwai AI Backend Online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
