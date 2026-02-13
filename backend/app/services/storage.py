import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
# 10 MB Limit
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Magic Numbers for strict validation
MAGIC_NUMBERS = {
    "jpg": b"\xFF\xD8\xFF",
    "jpeg": b"\xFF\xD8\xFF",
    "png": b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"
}

class StorageService:
    def __init__(self, upload_dir: Path = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, file: UploadFile):
        # 1. Check Extension
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 2. Check File Size (Seek to end, tell, then seek back)
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
             raise HTTPException(
                status_code=413, # Payload Too Large
                detail=f"File too large. Limit is {MAX_FILE_SIZE // (1024*1024)}MB."
            )

        # 3. Check Magic Numbers (Strict Header Check)
        header = file.file.read(8) # Read first 8 bytes
        file.file.seek(0) # Reset
        
        expected_magic = MAGIC_NUMBERS.get(ext.lstrip("."), b"")
        if not header.startswith(expected_magic):
             raise HTTPException(
                status_code=400, 
                detail="Invalid file content (Header mismatch). Potential malware detected."
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
            
        # Return URL-safe relative path for frontend/API
        return f"uploads/{unique_filename}"

    def resolve_path(self, relative_or_absolute_path: str) -> str:
        path = Path(relative_or_absolute_path)
        if path.is_absolute():
            return str(path)
        return str((BASE_DIR / path).resolve())

    def delete_file(self, file_path: str):
        path = Path(file_path)
        if path.exists():
            os.remove(path)
            return True
        return False

storage_service = StorageService()
