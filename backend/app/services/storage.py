import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path

UPLOAD_DIR = Path("backend/uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

class StorageService:
    def __init__(self, upload_dir: Path = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, filename: str):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        return ext

    async def save_file(self, file: UploadFile) -> str:
        """
        Saves an uploaded file to the local filesystem with a unique name.
        Returns the relative path to the file.
        """
        if not file.filename:
             raise HTTPException(status_code=400, detail="File must have a filename")

        ext = self._validate_file(file.filename)
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = self.upload_dir / unique_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        finally:
            await file.seek(0) # Reset cursor if needed elsewhere (though typically consumed here)
            
        # Return path relative to backend root, or just the filename depending on how we serve it.
        # Returning relative path for now.
        return str(file_path).replace("\\", "/")

    def delete_file(self, file_path: str):
        path = Path(file_path)
        if path.exists():
            os.remove(path)
            return True
        return False

storage_service = StorageService()
