from datetime import datetime
from pydantic import BaseModel
from app.models.ticket import TicketStatus
from app.schemas.user import UserResponse
from app.schemas.ticket_type import PriorityResponse, TicketTypeResponse


class TicketCreate(BaseModel):
    title: str
    description: str | None = None
    priority_id: int
    type_id: int
    department_id: int | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class StatusChangeRequest(BaseModel):
    status: TicketStatus
    comment: str | None = None


class AssignRequest(BaseModel):
    assignee_id: int | None = None
    department_id: int | None = None


class PriorityChangeRequest(BaseModel):
    priority_id: int


class TicketListItem(BaseModel):
    id: int
    number: str
    title: str
    status: TicketStatus
    priority_id: int
    type_id: int
    requester_id: int
    assignee_id: int | None = None
    department_id: int | None = None
    sla_deadline: datetime | None = None
    sla_violated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketResponse(BaseModel):
    id: int
    number: str
    title: str
    description: str | None = None
    status: TicketStatus
    priority_id: int
    type_id: int
    requester_id: int
    assignee_id: int | None = None
    department_id: int | None = None
    sla_deadline: datetime | None = None
    sla_paused_at: datetime | None = None
    sla_extra_minutes: int
    sla_violated: bool
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TicketHistoryResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int | None = None
    event_type: str
    payload: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
