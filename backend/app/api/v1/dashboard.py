from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, case

from app.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.utils.permissions import get_current_user

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard counters scoped by role."""
    base = select(
        func.count(Ticket.id).label("total"),
        func.sum(case((Ticket.status == TicketStatus.new, 1), else_=0)).label("new_count"),
        func.sum(case((Ticket.sla_violated.is_(True), 1), else_=0)).label("overdue"),
        func.sum(case((Ticket.status == TicketStatus.waiting_info, 1), else_=0)).label("waiting"),
    )

    if current_user.role == UserRole.user:
        # portal user — only their own tickets
        base = base.where(Ticket.requester_id == current_user.id)
    elif current_user.role == UserRole.agent:
        # agent — only tickets explicitly assigned to them
        base = base.where(Ticket.assignee_id == current_user.id)
    elif current_user.role == UserRole.department_head:
        # dept head — all tickets in their department
        if current_user.department_id is not None:
            base = base.where(Ticket.department_id == current_user.department_id)
        else:
            # no department assigned → show nothing (avoid confusion)
            base = base.where(Ticket.id == -1)
    # admin: no filter → sees everything

    row = (await db.execute(base)).one()

    return {
        "total": row.total or 0,
        "new_count": int(row.new_count or 0),
        "overdue": int(row.overdue or 0),
        "waiting": int(row.waiting or 0),
    }
