import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path
from PIL import Image, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_FILE_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}

MAGIC_NUMBERS = {
    "jpg": b"\xFF\xD8\xFF",
    "jpeg": b"\xFF\xD8\xFF",
    "png": b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
}

EXPECTED_FORMAT_BY_EXTENSION = {
    ".jpg": {"jpeg"},
    ".jpeg": {"jpeg"},
    ".png": {"png"},
    ".webp": {"webp"},
}


def _matches_magic(header: bytes, ext: str) -> bool:
    ext_key = ext.lstrip(".")
    if ext_key == "webp":
        # WEBP files are RIFF containers and encode WEBP at byte offsets 8..11
        return len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    expected_magic = MAGIC_NUMBERS.get(ext_key, b"")
    return header.startswith(expected_magic)

class StorageService:
    def __init__(self, upload_dir: Path = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, file: UploadFile):
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        content_type = (file.content_type or "").lower()

        # Some browser-side compression flows can send a blob-like filename
        # without extension. Infer extension from content type to avoid
        # rejecting valid images.
        if not ext and content_type in ("image/jpeg", "image/jpg"):
            ext = ".jpg"
        elif not ext and content_type == "image/png":
            ext = ".png"
        elif not ext and content_type == "image/webp":
            ext = ".webp"

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Invalid content type. Only JPEG, PNG, and WEBP images are allowed.",
            )
        
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
             raise HTTPException(
                status_code=413, # Payload Too Large
                detail=f"File too large. Limit is {MAX_FILE_SIZE // (1024*1024)}MB."
            )

        header = file.file.read(12)
        file.file.seek(0)

        if not _matches_magic(header, ext):
             raise HTTPException(
                status_code=400, 
                detail="Invalid file content (Header mismatch). Potential malware detected."
            )

        try:
            file.file.seek(0)
            image = Image.open(file.file)
            image.verify()
            detected_format = (image.format or "").lower()
        except (UnidentifiedImageError, OSError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid image payload. File is corrupted or not a real image.",
            )
        finally:
            file.file.seek(0)

        expected_formats = EXPECTED_FORMAT_BY_EXTENSION.get(ext, set())
        if detected_format not in expected_formats:
            raise HTTPException(
                status_code=400,
                detail="File extension does not match actual image format.",
            )

        return ext

    async def save_file(self, file: UploadFile) -> str:
        """
        Saves an uploaded file to the local filesystem with a unique name.
        Returns the relative path to the file.
        """
        if not file.filename:
             raise HTTPException(status_code=400, detail="File must have a filename")

        ext = self._validate_file(file)
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = self.upload_dir / unique_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        finally:
            await file.seek(0) # Reset cursor if needed elsewhere (though typically consumed here)
            
        return f"uploads/{unique_filename}"

    def resolve_path(self, relative_or_absolute_path: str) -> str:
        """Resolve a path and ensure it is jailed inside upload_dir.

        Raises HTTPException 400 for any path that escapes the upload directory,
        including absolute paths and directory traversal sequences (../../).
        """
        # Never allow absolute paths from untrusted input
        normalized = str(relative_or_absolute_path or "").replace("\\", "/").lstrip("/")
        path = Path(normalized)
        if path.is_absolute():
            raise HTTPException(status_code=400, detail="Absolute paths are not permitted.")

        # Allow callers to pass either "uploads/<file>" or just "<file>".
        # upload_dir already points at .../uploads, so keep only the inner path.
        if path.parts and path.parts[0] == self.upload_dir.name:
            path = Path(*path.parts[1:]) if len(path.parts) > 1 else Path("")

        if str(path) in ("", "."):
            raise HTTPException(status_code=400, detail="Invalid upload path.")

        resolved = (self.upload_dir / path).resolve()
        # Ensure the resolved path stays inside upload_dir
        try:
            resolved.relative_to(self.upload_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Path traversal detected.")

        return str(resolved)

    def delete_file(self, file_path: str):
        path = Path(file_path)
        if path.exists():
            os.remove(path)
            return True
        return False

storage_service = StorageService()
