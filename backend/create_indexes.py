import asyncio

from app.database import connect_to_mongo, close_mongo_connection, ensure_indexes


async def main() -> None:
    await connect_to_mongo()
    try:
        await ensure_indexes()
        print("[indexes] MongoDB indexes created/verified successfully")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
