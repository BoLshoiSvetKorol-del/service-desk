from datetime import datetime
from pydantic import BaseModel, field_validator


class RoutingRuleCreate(BaseModel):
    name: str
    keywords: str | None = None
    ticket_type_id: int | None = None
    department_id: int
    assignee_id: int | None = None
    priority: int = 0
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, v: str | None) -> str | None:
        if not v or not v.strip():
            return None
        # Normalize: strip each keyword, drop empty entries, rejoin
        parts = [k.strip() for k in v.split(",") if k.strip()]
        return ", ".join(parts) if parts else None


class RoutingRuleUpdate(BaseModel):
    name: str | None = None
    keywords: str | None = None
    ticket_type_id: int | None = None
    department_id: int | None = None
    assignee_id: int | None = None
    priority: int | None = None
    is_active: bool | None = None

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, v: str | None) -> str | None:
        if not v or not v.strip():
            return None
        parts = [k.strip() for k in v.split(",") if k.strip()]
        return ", ".join(parts) if parts else None


class RoutingRuleDepartmentInfo(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class RoutingRuleTicketTypeInfo(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class RoutingRuleAssigneeInfo(BaseModel):
    id: int
    full_name: str
    model_config = {"from_attributes": True}


class RoutingRuleResponse(BaseModel):
    id: int
    name: str
    keywords: str | None
    ticket_type_id: int | None
    department_id: int
    assignee_id: int | None
    priority: int
    is_active: bool
    created_at: datetime
    department: RoutingRuleDepartmentInfo
    ticket_type: RoutingRuleTicketTypeInfo | None
    assignee: RoutingRuleAssigneeInfo | None

    model_config = {"from_attributes": True}


class RoutingTestRequest(BaseModel):
    title: str
    description: str | None = None
    type_id: int | None = None


class RoutingTestResponse(BaseModel):
    matched: bool
    rule_id: int | None = None
    rule_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    assignee_id: int | None = None
    assignee_name: str | None = None
    fallback_used: bool = False
