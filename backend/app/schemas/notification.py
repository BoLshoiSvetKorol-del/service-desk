from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    ticket_id: int | None
    event_type: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
