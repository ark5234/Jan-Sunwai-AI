import asyncio
from datetime import datetime, timezone

from httpx import ASGITransport, AsyncClient

from app.auth import get_current_user
from app.config import settings
from main import app


async def _override_user():
    return {
        "_id": "mock-user-id",
        "username": "matrix_user",
        "email": "matrix@example.com",
        "full_name": "Matrix User",
        "phone_number": "+91-9999999999",
        "department": None,
        "job_title": None,
        "role": "citizen",
        "created_at": datetime.now(timezone.utc),
        "worker_status": None,
        "active_complaint_ids": [],
        "service_area": None,
        "is_approved": True,
    }


async def _run_matrix_checks() -> None:
    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            root = await client.get("/")
            assert root.status_code == 200
            assert root.json().get("message") == "Jan-Sunwai AI Backend Online"

            resp = await client.get("/api/v1/health/live")
            assert resp.status_code == 200
            assert resp.json().get("status") == "ok"

            legacy_resp = await client.get("/health/live")
            assert legacy_resp.status_code == 404

            me = await client.get("/api/v1/users/me")
            assert me.status_code == 200
            assert me.json().get("username") == "matrix_user"

            secured = await client.get("/api/v1/health/live")
            assert secured.headers.get("x-content-type-options") == "nosniff"
            assert secured.headers.get("x-frame-options") == "DENY"
            assert "content-security-policy" in secured.headers

            origin = settings.allowed_origins[0] if settings.allowed_origins else "http://localhost:5173"
            preflight = await client.options(
                "/api/v1/health/live",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert preflight.status_code in (200, 204)
            allow_origin = preflight.headers.get("access-control-allow-origin")
            if allow_origin:
                assert allow_origin in (origin, "*")
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_api_matrix():
    asyncio.run(_run_matrix_checks())
