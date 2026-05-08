from fastapi import UploadFile
from app.services.storage.base import StorageBackend


class MinIOStorage(StorageBackend):
    """Stub — interface only. Set STORAGE_BACKEND=minio and implement when needed."""

    async def save(self, file: UploadFile, ticket_id: int) -> tuple[str, int]:
        raise NotImplementedError("MinIO storage not implemented")

    async def delete(self, stored_path: str) -> None:
        raise NotImplementedError("MinIO storage not implemented")

    def get_url(self, stored_path: str) -> str:
        raise NotImplementedError("MinIO storage not implemented")
