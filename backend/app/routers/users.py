import asyncio
import hashlib
import secrets

from fastapi import APIRouter, HTTPException, Body, Depends, Request, Form
from app.database import get_database
from app.schemas import (
    UserCreate,
    UserResponse,
    UserRole,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ProfileUpdateRequest,
)
from app.auth import create_access_token, get_current_user
from app.config import settings
from app.rate_limiter import limiter
from app.services.sanitization import sanitize_text, sanitize_phone_number
from app.services.email_service import send_password_reset_email
from passlib.context import CryptContext
from bson import ObjectId
from datetime import datetime, timedelta, timezone

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/register")
@limiter.limit("5/minute")
async def register_user(request: Request, user: UserCreate = Body(...)):
    db = get_database()

    if user.role not in [UserRole.CITIZEN, UserRole.WORKER]:
        raise HTTPException(status_code=403, detail="Self-registration is allowed only for citizen or worker roles")
    
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
    if user_doc.get("full_name"):
        user_doc["full_name"] = sanitize_text(str(user_doc["full_name"]), max_len=100)
    if user_doc.get("phone_number"):
        user_doc["phone_number"] = sanitize_phone_number(str(user_doc["phone_number"]))
    user_doc["password"] = hashed_password
    user_doc["created_at"] = datetime.now(timezone.utc)

    # Worker-specific setup
    if user.role == UserRole.WORKER:
        user_doc["is_approved"] = False
        user_doc["worker_status"] = "offline"
        user_doc["active_complaint_ids"] = []
        # Persist service_area if provided
        if user.service_area:
            user_doc["service_area"] = user.service_area.model_dump()
    else:
        user_doc["role"] = UserRole.CITIZEN
        user_doc["is_approved"] = True

    # Insert
    new_user = await db["users"].insert_one(user_doc)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    created_user["_id"] = str(created_user["_id"])

    # Workers are NOT auto-logged-in — they must wait for admin approval
    if user.role == UserRole.WORKER:
        return {
            "message": "Worker registration submitted. Your account is pending admin approval.",
            "username": created_user["username"],
            "role": "worker",
            "is_approved": False,
        }

    # 4. Generate access token for auto-login (citizen only)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": created_user["username"], "role": created_user.get("role", "citizen")},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": created_user["username"],
        "role": created_user.get("role", "citizen"),
        "department": created_user.get("department")
    }


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    db = get_database()
    user = await db["users"].find_one({"username": username})
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "citizen")},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "username": user["username"], 
        "role": user.get("role", "citizen"),
        "department": user.get("department")
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
@limiter.limit("20/minute")
async def update_users_me(
    request: Request,
    payload: ProfileUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    updates: dict = {}

    if payload.full_name is not None:
        updates["full_name"] = sanitize_text(payload.full_name, max_len=100)
    if payload.phone_number is not None:
        updates["phone_number"] = sanitize_phone_number(payload.phone_number)

    if not updates:
        return current_user

    updates["updated_at"] = datetime.now(timezone.utc)
    updated = await db["users"].find_one_and_update(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": updates},
        return_document=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    updated["_id"] = str(updated["_id"])
    return updated


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest = Body(...)):
    db = get_database()
    # Always return the same response to avoid account enumeration.
    generic_msg = {
        "message": "If an account exists for this email, a password reset token has been issued."
    }

    user = await db["users"].find_one({"email": payload.email})
    if not user:
        return generic_msg

    await db["password_resets"].update_many(
        {"user_id": str(user["_id"]), "used": False},
        {"$set": {"used": True, "revoked_at": datetime.now(timezone.utc)}},
    )

    reset_token = secrets.token_urlsafe(32)
    await db["password_resets"].insert_one(
        {
            "user_id": str(user["_id"]),
            "token_hash": _hash_reset_token(reset_token),
            "used": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
    )

    await asyncio.to_thread(send_password_reset_email, payload.email, reset_token)
    return generic_msg


@router.post("/reset-password")
@limiter.limit("10/minute")
async def reset_password(request: Request, payload: ResetPasswordRequest = Body(...)):
    db = get_database()

    token_hash = _hash_reset_token(payload.token)
    reset_doc = await db["password_resets"].find_one(
        {"token_hash": token_hash, "used": False}
    )
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if reset_doc.get("expires_at") and reset_doc["expires_at"] < datetime.now(timezone.utc):
        await db["password_resets"].update_one(
            {"_id": reset_doc["_id"]},
            {"$set": {"used": True, "expired_at": datetime.now(timezone.utc)}},
        )
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = reset_doc.get("user_id")
    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid reset token state")

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": get_password_hash(payload.new_password), "updated_at": datetime.now(timezone.utc)}},
    )
    await db["password_resets"].update_one(
        {"_id": reset_doc["_id"]},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}},
    )

    return {"message": "Password reset successful"}
