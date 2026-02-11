from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_database
from app.schemas import UserCreate, UserResponse, UserInDB
from app.auth import create_access_token, get_current_user
from passlib.context import CryptContext
from bson import ObjectId
from datetime import timedelta
from datetime import datetime

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register")
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
    
    # 4. Generate access token for auto-login
    access_token_expires = timedelta(minutes=60 * 24)
    access_token = create_access_token(
        data={"sub": created_user["username"], "role": created_user.get("role", "citizen")},
        expires_delta=access_token_expires
    )
    
    # Return token along with user info (similar to login)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": created_user["username"],
        "role": created_user.get("role", "citizen")
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_database()
    user = await db["users"].find_one({"username": form_data.username})
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    access_token_expires = timedelta(minutes=60 * 24)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "citizen")},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "username": user["username"], 
        "role": user.get("role", "citizen")
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
