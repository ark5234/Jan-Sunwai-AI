from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import complaints, users
from app.database import connect_to_mongo, close_mongo_connection
import os
import time
import logging
from logging.handlers import RotatingFileHandler

# --- 1. Global Logging Setup ---
# Create logs directory
os.makedirs("backend/logs", exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JanSunwaiAI")

# File Handler (Rotate after 5MB, keep 3 backups)
file_handler = RotatingFileHandler("backend/logs/app.log", maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    logger.info("Starting up application...")
    await connect_to_mongo()
    yield
    # Shutdown: Close DB connection
    logger.info("Shutting down application...")
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

# CORS Setup (Allowing frontend to communicate)
# Allowed origins for development
origins = [
    "http://localhost:5173",  # Vite Frontend
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads for Static Access
os.makedirs("backend/uploads", exist_ok=True)
app.mount("/backend/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

# Include Routers
app.include_router(complaints.router, tags=["Complaints"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def read_root():
    return {"message": "Jan-Sunwai AI Backend Online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
