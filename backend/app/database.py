import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Check both MONGODB_URL and MONGO_URL for flexibility
MONGO_URL = settings.mongodb_url
DB_NAME = settings.db_name

class Database:
    client: AsyncIOMotorClient | None = None

db = Database()


async def ensure_indexes():
    if db.client is None:
        return
    database = db.client[DB_NAME]
    await database["users"].create_index("username", unique=True)
    await database["users"].create_index("email", unique=True)
    await database["complaints"].create_index([("user_id", 1), ("created_at", -1)])
    await database["complaints"].create_index([("status", 1), ("created_at", -1)])
    await database["complaints"].create_index([("department", 1), ("created_at", -1)])
    await database["complaints"].create_index("authority_id")

async def connect_to_mongo():
    try:
        db.client = AsyncIOMotorClient(MONGO_URL)
        # Verify connection
        await db.client.admin.command('ping')
        await ensure_indexes()
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
