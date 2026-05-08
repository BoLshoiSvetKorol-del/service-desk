from datetime import datetime
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentWithAgents(DepartmentResponse):
    agents: list["UserBrief"] = []


class UserBrief(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}


DepartmentWithAgents.model_rebuild()
