from abc import ABC, abstractmethod
from fastapi import UploadFile


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, ticket_id: int) -> tuple[str, int]:
        """Save file, return (stored_path, size_bytes)."""

    @abstractmethod
    async def delete(self, stored_path: str) -> None:
        """Delete file by stored path."""

    @abstractmethod
    def get_url(self, stored_path: str) -> str:
        """Return URL or X-Accel-Redirect path for the file."""
