import motor.motor_asyncio, asyncio, passlib.context
async def do_fix():
 db = motor.motor_asyncio.AsyncIOMotorClient().jan_sunwai_db
 pwd_c = passlib.context.CryptContext(schemes=['bcrypt'], deprecated='auto')
 for name, pwd in [('worker_gujarat', 'gujarat123'), ('worker_maharashtra', 'maha123'), ('worker_demo', 'worker123')]:
  print(f'fixing {name}')
  await db.users.update_one({'username': name}, {'$set': {'password': pwd_c.hash(pwd)}})
asyncio.run(do_fix())
