import os
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Check both MONGODB_URL and MONGO_URL for flexibility
MONGO_URL = settings.mongodb_url
DB_NAME = settings.db_name

# BL-07: Explicit connection pool configuration.
# Motor default is 100 max connections — fine for small deployments but
# should be tuned for production based on expected concurrency.
_MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
_MONGO_MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "5"))


class Database:
    client: AsyncIOMotorClient | None = None


db = Database()


def _safe_mongo_target(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 27017
        db_name = (parsed.path or "").lstrip("/") or DB_NAME
        return f"{host}:{port}/{db_name}"
    except Exception:
        return "<unavailable>"


async def ensure_indexes():
    if db.client is None:
        return
    database = db.client[DB_NAME]

    # User indexes
    await database["users"].create_index("username", unique=True)
    await database["users"].create_index("email", unique=True)

    # Complaint indexes
    await database["complaints"].create_index([("user_id", 1), ("created_at", -1)])
    await database["complaints"].create_index([("status", 1), ("created_at", -1)])
    await database["complaints"].create_index([("department", 1), ("created_at", -1)])
    await database["complaints"].create_index("authority_id")

    # BL-06: Compound index for the escalation loop query.
    # Without this, run_escalation_check() does a full collection scan every hour.
    # Covers: {"status": {$in: [...]}, "escalated": {$ne: True}, "created_at": {$lte: ...}}
    await database["complaints"].create_index(
        [("status", 1), ("escalated", 1), ("created_at", 1)],
        name="escalation_loop_idx",
    )

    # Notification indexes
    await database["notifications"].create_index([("user_id", 1), ("created_at", -1)])
    await database["notifications"].create_index([("user_id", 1), ("is_read", 1)])

    # Password reset indexes
    await database["password_resets"].create_index([("token_hash", 1)], unique=True)
    await database["password_resets"].create_index([("user_id", 1), ("used", 1)])
    await database["password_resets"].create_index("expires_at", expireAfterSeconds=0)

    # P3-A: TTL index for LLM job results (expire after 1 hour)
    await database["llm_jobs"].create_index("created_at", expireAfterSeconds=3600)


async def connect_to_mongo():
    try:
        db.client = AsyncIOMotorClient(
            MONGO_URL,
            # BL-07: Explicit pool sizes for predictable connection management
            maxPoolSize=_MONGO_MAX_POOL_SIZE,
            minPoolSize=_MONGO_MIN_POOL_SIZE,
        )
        # Verify connection
        await db.client.admin.command("ping")
        await ensure_indexes()
        print(f"Connected to MongoDB at {_safe_mongo_target(MONGO_URL)}")
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
