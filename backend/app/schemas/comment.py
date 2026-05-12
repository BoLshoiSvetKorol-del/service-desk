from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator


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
    author_name: str | None = None
    author_role: str | None = None
    body: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _extract_author(cls, data):
        if isinstance(data, dict):
            return data
        c = data
        author_name = None
        author_role = None
        if c.author:
            author_name = c.author.full_name or c.author.username
            author_role = c.author.role.value if c.author.role else None
        return {
            "id": c.id,
            "ticket_id": c.ticket_id,
            "author_id": c.author_id,
            "author_name": author_name,
            "author_role": author_role,
            "body": c.body,
            "is_internal": c.is_internal,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
