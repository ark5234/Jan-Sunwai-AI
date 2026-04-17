"""
Re-hash passwords for all existing users in MongoDB.

Run from backend/ directory:
    python -X utf8 rehash_passwords.py

This script:
1. Fetches every user from the DB
2. Determines their plain-text password from the known demo credential table
3. Re-hashes it with bcrypt (the same scheme used by users.py)
4. Writes the new hash back to the DB

"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone

MONGODB_URL = os.getenv("MONGODB_URL") or os.getenv("MONGO_URL") or "mongodb://localhost:27017"
DATABASE_NAME = os.getenv("DB_NAME", "jan_sunwai_db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Known plain-text passwords per username (base accounts)
KNOWN_PASSWORDS: dict[str, str] = {
    "admin_demo":   "admin123",
    "citizen_demo": "citizen123",
}

# Dept prefix → password for all dept_head / worker accounts
DEPT_PREFIXES = {
    "Health Department":    "health123",
    "Civil Department":     "civil123",
    "Horticulture":         "horti123",
    "Electrical Department":"elec123",
    "IT Department":        "it123",
    "Commercial":           "comm123",
    "Enforcement":          "enf123",
    "VBD Department":       "vbd123",
    "EBR Department":       "ebr123",
    "Fire Department":      "fire123",
}


def resolve_password(user: dict) -> str | None:
    username = user.get("username", "")
    role     = user.get("role", "")
    dept     = user.get("department", "")

    # 1. Explicit known accounts
    if username in KNOWN_PASSWORDS:
        return KNOWN_PASSWORDS[username]

    # 2. Dept staff — password is the dept prefix + "123"
    if role in ("dept_head", "worker") and dept in DEPT_PREFIXES:
        return DEPT_PREFIXES[dept]

    # 3. Any other citizen — we don't know their original password,
    #    skip re-hashing so we don't overwrite a real user's creds.
    return None


async def rehash_all():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    users = await db["users"].find({}).to_list(length=None)
    print(f"Found {len(users)} users in DB.\n")

    updated = 0
    skipped = 0

    for user in users:
        plain = resolve_password(user)
        if plain is None:
            print(f"  ⚠  SKIP  {user.get('username'):30s} — unknown password, not touching.")
            skipped += 1
            continue

        new_hash = pwd_context.hash(plain)
        await db["users"].update_one(
            {"_id": user["_id"]},
            {"$set": {"password": new_hash, "updated_at": datetime.now(timezone.utc)}},
        )
        print(f"  ✓  OK    {user.get('username'):30s} → [{plain}]")
        updated += 1

    client.close()
    print(f"\n{'='*60}")
    print(f"Done.  Updated: {updated}  |  Skipped: {skipped}")
    print(f"{'='*60}\n")
    print("You can now log in with:")
    print("  admin_demo   / admin123")
    print("  citizen_demo / citizen123")
    print("  <dept>_<role> / <dept-prefix>123  (e.g. civil_jengineer / civil123)")


if __name__ == "__main__":
    asyncio.run(rehash_all())
