import os
from motor.motor_asyncio import AsyncIOMotorClient

# Check both MONGODB_URL and MONGO_URL for flexibility
MONGO_URL = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
DB_NAME = "jan_sunwai_db"

class Database:
    client: AsyncIOMotorClient | None = None

db = Database()

async def connect_to_mongo():
    try:
        db.client = AsyncIOMotorClient(MONGO_URL)
        # Verify connection
        await db.client.admin.command('ping')
        print(f"Connected to MongoDB at {MONGO_URL}")
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("MongoDB connection closed")

def get_database():
    """Returns the database instance."""
    if db.client is None:
        raise RuntimeError("Database client not initialized. Ensure MongoDB is running and app started correctly.")
    return db.client[DB_NAME]
