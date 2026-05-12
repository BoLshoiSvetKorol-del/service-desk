from datetime import datetime
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    comment_id: int | None
    original_filename: str
    size_bytes: int
    mimetype: str
    uploaded_by: int | None
    uploader_name: str | None = None
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}
