import uuid
import os
from pathlib import Path
from fastapi import UploadFile
from app.services.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, upload_path: str):
        self.upload_path = Path(upload_path)

    async def save(self, file: UploadFile, ticket_id: int) -> tuple[str, int]:
        dest_dir = self.upload_path / "tickets" / str(ticket_id)
        dest_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(file.filename or "file").name
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        dest = dest_dir / stored_name

        content = await file.read()
        dest.write_bytes(content)

        # stored_path relative to upload_path root for X-Accel-Redirect
        rel = dest.relative_to(self.upload_path)
        return str(rel).replace("\\", "/"), len(content)

    async def delete(self, stored_path: str) -> None:
        full = self.upload_path / stored_path
        if full.exists():
            full.unlink()

    def get_url(self, stored_path: str) -> str:
        # Nginx serves /uploads/** via X-Accel-Redirect → /internal/uploads/**
        return f"/uploads/{stored_path}"
