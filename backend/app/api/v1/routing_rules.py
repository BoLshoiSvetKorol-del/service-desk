from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.routing_rule import RoutingRule
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.routing_rule import (
    RoutingRuleCreate, RoutingRuleUpdate, RoutingRuleResponse,
    RoutingTestRequest, RoutingTestResponse,
)
from app.services.routing_service import find_matching_rule
from app.utils.permissions import require_role

router = APIRouter()


@router.get("", response_model=list[RoutingRuleResponse])
async def list_routing_rules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(
        select(RoutingRule).order_by(RoutingRule.priority.asc(), RoutingRule.id.asc())
    )
    return result.scalars().all()


@router.post("", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_routing_rule(
    data: RoutingRuleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    dept = await db.get(Department, data.department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Отдел не найден")

    if data.assignee_id is not None:
        agent = await db.get(User, data.assignee_id)
        if not agent or agent.role == UserRole.user:
            raise HTTPException(status_code=404, detail="Исполнитель не найден")

    rule = RoutingRule(
        name=data.name,
        keywords=data.keywords,
        ticket_type_id=data.ticket_type_id,
        department_id=data.department_id,
        assignee_id=data.assignee_id,
        priority=data.priority,
        is_active=data.is_active,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RoutingRuleResponse)
async def update_routing_rule(
    rule_id: int,
    data: RoutingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    rule = await db.get(RoutingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Правило маршрутизации не найдено")

    if data.name is not None:
        rule.name = data.name
    if "keywords" in data.model_fields_set:
        rule.keywords = data.keywords
    if "ticket_type_id" in data.model_fields_set:
        rule.ticket_type_id = data.ticket_type_id
    if data.priority is not None:
        rule.priority = data.priority
    if data.is_active is not None:
        rule.is_active = data.is_active

    if data.department_id is not None:
        dept = await db.get(Department, data.department_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Отдел не найден")
        rule.department_id = data.department_id

    if "assignee_id" in data.model_fields_set:
        if data.assignee_id is not None:
            agent = await db.get(User, data.assignee_id)
            if not agent or agent.role == UserRole.user:
                raise HTTPException(status_code=404, detail="Исполнитель не найден")
        rule.assignee_id = data.assignee_id

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routing_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    rule = await db.get(RoutingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Правило маршрутизации не найдено")
    await db.delete(rule)
    await db.commit()


@router.post("/test", response_model=RoutingTestResponse)
async def test_routing(
    data: RoutingTestRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    """Dry-run: show which rule would be applied for a given ticket."""
    rule = await find_matching_rule(db, data.title, data.description, data.type_id)
    if rule:
        return RoutingTestResponse(
            matched=True,
            rule_id=rule.id,
            rule_name=rule.name,
            department_id=rule.department_id,
            department_name=rule.department.name,
            assignee_id=rule.assignee_id,
            assignee_name=rule.assignee.full_name if rule.assignee else None,
        )
    return RoutingTestResponse(matched=False, fallback_used=True)
