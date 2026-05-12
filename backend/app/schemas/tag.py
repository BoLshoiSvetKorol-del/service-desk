from datetime import datetime
from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color_hex: str = Field(default="#1677ff", pattern=r"^#[0-9a-fA-F]{6}$")


class TagResponse(BaseModel):
    id: int
    name: str
    color_hex: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketNoteCreate(BaseModel):
    body: str = Field(min_length=1)


class TicketNoteUpdate(BaseModel):
    body: str = Field(min_length=1)


class TicketNoteResponse(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SetTagsRequest(BaseModel):
    tag_ids: list[int]
