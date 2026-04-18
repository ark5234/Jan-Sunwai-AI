import asyncio
import os
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def run():
    url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(url)
    db = client["jan_sunwai_db"]
    
    # 1. Recreate 'vikrant'
    hashed_pwd = pwd_context.hash("vikrant123")
    await db.users.update_one(
        {"username": "vikrant"},
        {"$set": {"role": "citizen", "disabled": False, "password": hashed_pwd}},
        upsert=True
    )
    
    vikrant_user = await db.users.find_one({"username": "vikrant"})
    vid = str(vikrant_user["_id"])
    
    # 2. Insert mock complaints
    now = datetime.now(timezone.utc)
    mock = [
        {
            "description": "Road has huge crater near the park.",
            "status": "Open",
            "department": "Civil Department",
            "severity": "Medium",
            "user_id": vid,
            "created_at": (now - timedelta(days=2)).isoformat(),
            "updated_at": (now - timedelta(days=2)).isoformat(),
            "location": {"address": "MG Road, Park Area", "coordinates": {"lat": 23.0, "lon": 72.0}},
            "image_url": "uploads/stub1.jpg",
            "ai_metadata": {"confidence": 0.95}
        },
        {
            "description": "Street lights not working for a week.",
            "status": "In Progress",
            "department": "Electrical Department",
            "severity": "Low",
            "user_id": vid,
            "created_at": (now - timedelta(days=1)).isoformat(),
            "updated_at": now.isoformat(),
            "location": {"address": "Street 5, Area 2", "coordinates": {"lat": 23.1, "lon": 72.1}},
            "image_url": "uploads/stub2.jpg",
            "ai_metadata": {"confidence": 0.88}
        }
    ]
    await db.complaints.insert_many(mock)
    print("MOCK DATA CREATED: 'vikrant' (pwd: vikrant123) and 2 test complaints generated.")

if __name__ == "__main__":
    asyncio.run(run())
