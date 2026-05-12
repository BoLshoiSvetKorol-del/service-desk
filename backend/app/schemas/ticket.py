from datetime import datetime
from pydantic import BaseModel, model_validator
from app.models.ticket import TicketStatus
from app.schemas.tag import TagResponse


class PriorityEmbedded(BaseModel):
    id: int
    name: str  # level value: low/normal/high/critical
    sla_hours: int
    color_hex: str


class TicketCreate(BaseModel):
    title: str
    description: str | None = None
    priority_id: int | None = None
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


class MergeRequest(BaseModel):
    target_id: int
    comment: str | None = None


def _prio_embedded(prio) -> dict:
    return {
        "id": prio.id,
        "name": prio.level.value,
        "sla_hours": prio.sla_hours,
        "color_hex": prio.color_hex,
    }


class TicketListItem(BaseModel):
    id: int
    number: str
    title: str
    status: TicketStatus
    priority: PriorityEmbedded
    ticket_type_id: int | None = None
    ticket_type_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    assignee_id: int | None = None
    assignee_name: str | None = None
    creator_id: int
    creator_name: str
    sla_deadline: datetime | None = None
    sla_violated: bool
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _map_from_orm(cls, data):
        if isinstance(data, dict):
            return data
        t = data
        return {
            "id": t.id,
            "number": t.number,
            "title": t.title,
            "status": t.status,
            "priority": _prio_embedded(t.priority),
            "ticket_type_id": t.type_id,
            "ticket_type_name": t.ticket_type.name if t.ticket_type else None,
            "department_id": t.department_id,
            "department_name": t.department.name if t.department else None,
            "assignee_id": t.assignee_id,
            "assignee_name": (t.assignee.full_name or t.assignee.username) if t.assignee else None,
            "creator_id": t.requester_id,
            "creator_name": (t.requester.full_name or t.requester.username) if t.requester else "",
            "sla_deadline": t.sla_deadline,
            "sla_violated": t.sla_violated,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "tags": list(t.tags),
        }


class TicketResponse(BaseModel):
    id: int
    number: str
    title: str
    description: str | None = None
    status: TicketStatus
    priority: PriorityEmbedded
    ticket_type_id: int | None = None
    ticket_type_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    assignee_id: int | None = None
    assignee_name: str | None = None
    creator_id: int
    creator_name: str
    sla_deadline: datetime | None = None
    sla_paused_at: datetime | None = None
    sla_extra_minutes: int
    sla_violated: bool
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    merged_into_id: int | None = None
    tags: list[TagResponse] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _map_from_orm(cls, data):
        if isinstance(data, dict):
            return data
        t = data
        return {
            "id": t.id,
            "number": t.number,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": _prio_embedded(t.priority),
            "ticket_type_id": t.type_id,
            "ticket_type_name": t.ticket_type.name if t.ticket_type else None,
            "department_id": t.department_id,
            "department_name": t.department.name if t.department else None,
            "assignee_id": t.assignee_id,
            "assignee_name": (t.assignee.full_name or t.assignee.username) if t.assignee else None,
            "creator_id": t.requester_id,
            "creator_name": (t.requester.full_name or t.requester.username) if t.requester else "",
            "sla_deadline": t.sla_deadline,
            "sla_paused_at": t.sla_paused_at,
            "sla_extra_minutes": t.sla_extra_minutes,
            "sla_violated": t.sla_violated,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "closed_at": t.closed_at,
            "merged_into_id": t.merged_into_id,
            "tags": list(t.tags),
        }


class TicketHistoryResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int | None = None
    user_name: str | None = None
    event_type: str
    payload: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _extract_actor(cls, data):
        if isinstance(data, dict):
            return data
        h = data
        user_name = None
        if h.actor:
            user_name = h.actor.full_name or h.actor.username
        return {
            "id": h.id,
            "ticket_id": h.ticket_id,
            "user_id": h.user_id,
            "user_name": user_name,
            "event_type": h.event_type,
            "payload": h.payload,
            "created_at": h.created_at,
        }
