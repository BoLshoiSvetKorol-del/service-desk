from pydantic import BaseModel
from app.models.priority import PriorityLevel


class PriorityResponse(BaseModel):
    id: int
    level: PriorityLevel
    name: str
    sla_hours: int
    color_hex: str

    model_config = {"from_attributes": True}


class TicketTypeCreate(BaseModel):
    name: str
    service_type: str | None = None
    work_direction: str | None = None
    default_department_id: int | None = None
    is_active: bool = True


class TicketTypeUpdate(BaseModel):
    name: str | None = None
    service_type: str | None = None
    work_direction: str | None = None
    default_department_id: int | None = None
    is_active: bool | None = None


class TicketTypeResponse(BaseModel):
    id: int
    name: str
    service_type: str | None = None
    work_direction: str | None = None
    default_department_id: int | None = None
    is_active: bool

    model_config = {"from_attributes": True}
