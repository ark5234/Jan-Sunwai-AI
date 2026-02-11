from fastapi import APIRouter, HTTPException, Body
from app.database import get_database
from app.schemas import UserCreate, UserResponse, UserInDB
from passlib.context import CryptContext
from bson import ObjectId
from datetime import datetime

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate = Body(...)):
    db = get_database()
    
    # 1. Check if user already exists
    existing_user = await db["users"].find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    existing_email = await db["users"].find_one({"email": user.email})
    if existing_email:
         raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash Password
    hashed_password = get_password_hash(user.password)
    
    # 3. Create User Document
    user_doc = user.model_dump()
    user_doc["password"] = hashed_password
    user_doc["created_at"] = datetime.utcnow() # Add creation timestamp
    
    # Insert
    new_user = await db["users"].insert_one(user_doc)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    
    # Fix ObjectId and ensure response matches schema
    created_user["_id"] = str(created_user["_id"])
    
    return created_user

@router.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    db = get_database()
    user = await db["users"].find_one({"username": username})
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    return {"message": "Login successful", "username": user["username"], "role": user["role"]}
