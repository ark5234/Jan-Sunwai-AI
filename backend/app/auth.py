"""
P4-E: httpOnly cookie-based auth support added alongside existing Bearer token.

Strategy: dual-mode auth
  - Backend issues a Lax/Strict httpOnly cookie on login (XSS-safe)
  - Frontend uses credentials: 'include' — no more localStorage token
  - Bearer token still accepted for API clients / backwards compat during transition
  - Token in response body retained for 3-month deprecation window (remove 2026-07-17)
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from app.database import get_database
from app.schemas import UserRole
from app.config import settings

# Configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Cookie name used by set_auth_cookie / clear_auth_cookie
AUTH_COOKIE_NAME = "js_access_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login", auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def set_auth_cookie(response, token: str) -> None:
    """
    P4-E: Set httpOnly cookie — inaccessible to JavaScript, preventing XSS token theft.
    SameSite=Lax allows navigation-triggered GET requests but blocks CSRF on mutations.
    Use Strict for highest security if you control all cross-origin flows.
    """
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,   # HTTPS-only in production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response) -> None:
    """Clear the auth cookie on logout."""
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")


def _extract_token(request: Request, bearer_token: str | None) -> str | None:
    """
    P4-E: Try httpOnly cookie first (preferred), then fall back to Bearer header.
    This dual-mode allows the transition period where old clients still use
    Authorization: Bearer while new clients use the cookie.
    """
    # 1. Cookie (preferred — XSS-safe)
    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    # 2. Bearer header (legacy / API clients)
    return bearer_token


async def get_current_user(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
):
    token = _extract_token(request, bearer_token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = get_database()
    user = await db["users"].find_one({"username": username})
    if user is None:
        raise credentials_exception

    # Fix ID
    user["_id"] = str(user["_id"])
    return user


# Role-based permission dependencies
async def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Require ADMIN role"""
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_dept_head(current_user: dict = Depends(get_current_user)):
    """Require DEPT_HEAD role"""
    if current_user.get("role") != UserRole.DEPT_HEAD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department Head access required"
        )
    return current_user


async def get_current_admin_or_dept_head(current_user: dict = Depends(get_current_user)):
    """Require ADMIN or DEPT_HEAD role"""
    role = current_user.get("role")
    if role not in [UserRole.ADMIN, UserRole.DEPT_HEAD]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Department Head access required"
        )
    return current_user


async def get_current_worker(current_user: dict = Depends(get_current_user)):
    """Require WORKER role. Blocks login if not yet approved by admin."""
    if current_user.get("role") != UserRole.WORKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Worker access required"
        )
    if not current_user.get("is_approved", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your worker account is pending admin approval. Please wait for approval before logging in.",
        )
    return current_user


async def get_current_admin_or_worker(current_user: dict = Depends(get_current_user)):
    """Require ADMIN or approved WORKER role"""
    role = current_user.get("role")
    if role == UserRole.WORKER and not current_user.get("is_approved", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your worker account is pending admin approval.",
        )
    if role not in [UserRole.ADMIN, UserRole.WORKER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Worker access required"
        )
    return current_user
