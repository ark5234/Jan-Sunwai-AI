from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import complaints, users
from app.database import connect_to_mongo, close_mongo_connection
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    await connect_to_mongo()
    yield
    # Shutdown: Close DB connection
    await close_mongo_connection()

app = FastAPI(title="Jan-Sunwai AI API", version="1.0.0", lifespan=lifespan)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )

# CORS Setup (Allowing frontend to communicate)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
