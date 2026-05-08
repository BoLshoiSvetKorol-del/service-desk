from datetime import datetime
from pydantic import BaseModel


class TicketsCountItem(BaseModel):
    period: str
    count: int


class TicketsCountResponse(BaseModel):
    items: list[TicketsCountItem]
    total: int


class StatusDistributionItem(BaseModel):
    status: str
    count: int


class AvgResolutionItem(BaseModel):
    priority: str
    avg_hours: float | None


class SLAComplianceResponse(BaseModel):
    total: int
    compliant: int
    compliance_rate: float


class SavedFilterCreate(BaseModel):
    name: str
    filter_params: dict = {}


class SavedFilterResponse(BaseModel):
    id: int
    user_id: int
    name: str
    filter_params: dict
    created_at: datetime

    model_config = {"from_attributes": True}
