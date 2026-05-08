from datetime import datetime
from pydantic import BaseModel, field_validator


class CommentCreate(BaseModel):
    body: str
    is_internal: bool = False

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Комментарий не может быть пустым")
        return v


class CommentUpdate(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Комментарий не может быть пустым")
        return v


class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    author_id: int | None
    body: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
