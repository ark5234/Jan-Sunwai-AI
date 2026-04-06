import motor.motor_asyncio, asyncio
async def check():
 db = motor.motor_asyncio.AsyncIOMotorClient().jan_sunwai_db
 user = await db.users.find_one({'username': 'worker_gujarat'})
 print(user)
asyncio.run(check())
