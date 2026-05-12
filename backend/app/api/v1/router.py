from fastapi import APIRouter
from app.api.v1 import (
    auth, users, departments, priorities, ticket_types,
    tickets, comments, attachments, filters, reports,
    events, notifications, tags, notes,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(priorities.router, prefix="/priorities", tags=["priorities"])
api_router.include_router(ticket_types.router, prefix="/ticket-types", tags=["ticket-types"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(comments.router, prefix="/tickets", tags=["comments"])
api_router.include_router(attachments.router, prefix="", tags=["attachments"])
api_router.include_router(filters.router, prefix="/filters", tags=["filters"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(events.router, prefix="", tags=["events"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(notes.router, prefix="", tags=["notes"])
