import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['jan_sunwai_db']
    user = await db['users'].find_one({'username': 'health_cmo'})
    if not user:
        print("User not found!")
    else:
        print(f"Found user: {user['username']}")
        print(f"Role: {user['role']}")
        is_valid = pwd_context.verify('health123', user['password'])
        print(f"Password 'health123' valid? {is_valid}")
        print(f"Password 'healthworker123' valid? {pwd_context.verify('healthworker123', user['password'])}")
        print(f"Is Approved: {user.get('is_approved')}")

if __name__ == '__main__':
    asyncio.run(test())
