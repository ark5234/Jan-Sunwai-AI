import asyncio
import io

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image, features
from starlette.requests import Request

from app.routers import complaints, health
from app.services.sanitization import sanitize_text
from app.services.storage import StorageService


def _make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(120, 140, 160)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), color=(20, 160, 120)).save(buf, format="PNG")
    return buf.getvalue()


def _make_webp_bytes() -> bytes:
    if not features.check("webp"):
        pytest.skip("WebP codec is not available in this Pillow build")
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), color=(80, 120, 200)).save(buf, format="WEBP")
    return buf.getvalue()


def _make_upload(filename: str, data: bytes, content_type: str | None = None) -> UploadFile:
    headers = {"content-type": content_type} if content_type else None
    return UploadFile(filename=filename, file=io.BytesIO(data), headers=headers)


def _dummy_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/analyze",
        "headers": [],
    }
    return Request(scope)


def test_storage_rejects_magic_number_mismatch(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    fake_jpeg = _make_upload("fake.jpg", b"not-a-valid-jpeg-header")

    with pytest.raises(HTTPException) as exc:
        service._validate_file(fake_jpeg)

    assert exc.value.status_code == 400
    assert "Header mismatch" in exc.value.detail


def test_storage_accepts_valid_jpeg_magic_number(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    valid_jpeg = _make_upload("valid.jpg", _make_jpeg_bytes())

    ext = service._validate_file(valid_jpeg)
    assert ext == ".jpg"


def test_storage_accepts_valid_png_magic_number(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    valid_png = _make_upload("valid.png", _make_png_bytes())

    ext = service._validate_file(valid_png)
    assert ext == ".png"


def test_storage_accepts_valid_webp_magic_number(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    valid_webp = _make_upload("valid.webp", _make_webp_bytes())

    ext = service._validate_file(valid_webp)
    assert ext == ".webp"


def test_storage_accepts_missing_extension_with_jpeg_content_type(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    blob_upload = _make_upload("blob", _make_jpeg_bytes(), "image/jpeg")

    ext = service._validate_file(blob_upload)
    assert ext == ".jpg"


def test_storage_rejects_corrupt_jpeg_payload_with_valid_magic(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    # Starts with JPEG magic bytes but not actually decodable as a JPEG image.
    corrupted = _make_upload("corrupt.jpg", b"\xff\xd8\xffthis-is-not-a-valid-jpeg")

    with pytest.raises(HTTPException) as exc:
        service._validate_file(corrupted)

    assert exc.value.status_code == 400
    assert "Invalid image payload" in exc.value.detail


def test_storage_rejects_oversized_upload(tmp_path):
    service = StorageService(upload_dir=tmp_path)
    big_payload = b"\xff\xd8\xff" + (b"0" * (25 * 1024 * 1024 + 16))
    oversized = _make_upload("big.jpg", big_payload)

    with pytest.raises(HTTPException) as exc:
        service._validate_file(oversized)

    assert exc.value.status_code == 413
    assert "File too large" in exc.value.detail


def test_analyze_returns_503_when_classifier_fails(monkeypatch):
    async def fake_save_file(_file):
        return "uploads/fake.jpg"

    def fake_resolve_path(_path):
        return "uploads/fake.jpg"

    def fake_classify(_path):
        return {"method": "error", "error": "ollama unreachable"}

    monkeypatch.setattr(complaints.storage_service, "save_file", fake_save_file)
    monkeypatch.setattr(complaints.storage_service, "resolve_path", fake_resolve_path)
    monkeypatch.setattr(complaints.classifier, "classify", fake_classify)

    response = asyncio.run(
        complaints.analyze_complaint(
            request=_dummy_request(),
            file=_make_upload("sample.jpg", _make_jpeg_bytes()),
            language="en",
            current_user={"username": "citizen1", "_id": "u1"},
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 503
    payload = bytes(response.body).decode("utf-8")
    assert "AI analysis unavailable" in payload
    assert "retryable" in payload


def test_ready_check_reports_degraded_when_db_ping_fails(monkeypatch):
    class _FailingDB:
        async def command(self, _name):
            raise RuntimeError("database is down")

    monkeypatch.setattr(health, "get_database", lambda: _FailingDB())
    result = asyncio.run(health.ready_check())

    assert result["status"] == "degraded"
    assert result["database"]["ok"] is False
    assert "error" not in result["database"]


def test_sanitize_text_preserves_text_without_html_escaping():
    payload = "<script>alert('xss')</script>"
    sanitized = sanitize_text(payload)

    assert sanitized == payload
