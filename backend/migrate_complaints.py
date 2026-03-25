import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
DATABASE_NAME = os.getenv("DB_NAME", "jan_sunwai_db")

# Mapping old department names to the new official hierarchy
MIGRATION_MAP = {
    "Municipal - PWD (Roads)": "Civil Department",
    "Municipal - Street Lighting": "Electrical Department",
    "Municipal - Sanitation": "Health Department",
    "Municipal - Water & Sewerage": "Civil Department",
    "Utility - Power (DISCOM)": "Electrical Department",
    "Police - Traffic": "Enforcement",
    "Police - Local Law Enforcement": "Enforcement",
    "Pollution Control Board": "Health Department",
    "State Transport": "Civil Department",
    "Municipal - Horticulture": "Horticulture",
    "Unknown": "Uncategorized"
}

async def migrate_complaints():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("🔄 Starting legacy complaints migration...")
    
    total_modified = 0
    for old_dept, new_dept in MIGRATION_MAP.items():
        result = await db["complaints"].update_many(
            {"department": old_dept},
            {"$set": {"department": new_dept}}
        )
        if result.modified_count > 0:
            print(f"  ✅ Migrated {result.modified_count} complaints from '{old_dept}' -> '{new_dept}'")
            total_modified += result.modified_count
            
    print(f"\n🎉 Migration complete. {total_modified} total complaints updated.")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_complaints())
