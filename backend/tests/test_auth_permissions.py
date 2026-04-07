import asyncio
from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app import auth
from app.schemas import UserRole


def test_create_access_token_includes_expected_claims():
    token = auth.create_access_token(
        {"sub": "alice", "role": "citizen"},
        expires_delta=timedelta(minutes=5),
    )
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])

    assert payload["sub"] == "alice"
    assert payload["role"] == "citizen"
    assert "exp" in payload


def test_get_current_admin_rejects_non_admin():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_current_admin({"role": UserRole.CITIZEN}))

    assert exc.value.status_code == 403
    assert "Admin access required" in exc.value.detail


def test_get_current_admin_accepts_admin():
    user = asyncio.run(auth.get_current_admin({"role": UserRole.ADMIN}))
    assert user["role"] == UserRole.ADMIN


def test_get_current_worker_rejects_unapproved_worker():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.get_current_worker({"role": UserRole.WORKER, "is_approved": False}))

    assert exc.value.status_code == 403
    assert "pending admin approval" in exc.value.detail


def test_get_current_admin_or_worker_accepts_approved_worker():
    user = asyncio.run(auth.get_current_admin_or_worker({"role": UserRole.WORKER, "is_approved": True}))
    assert user["role"] == UserRole.WORKER


def test_get_current_admin_or_dept_head_accepts_dept_head():
    user = asyncio.run(auth.get_current_admin_or_dept_head({"role": UserRole.DEPT_HEAD}))
    assert user["role"] == UserRole.DEPT_HEAD
