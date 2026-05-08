from app.services.storage.base import StorageBackend


def get_storage() -> StorageBackend:
    from app.config import settings
    if settings.STORAGE_BACKEND == "minio":
        from app.services.storage.minio import MinIOStorage
        return MinIOStorage()
    from app.services.storage.local import LocalStorage
    return LocalStorage(settings.UPLOAD_PATH)
