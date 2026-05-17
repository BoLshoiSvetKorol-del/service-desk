"""performance: indexes on tickets and related tables

Revision ID: 016
Revises: 015
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tickets — поля фильтрации и сортировки
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_department_id", "tickets", ["department_id"])
    op.create_index("ix_tickets_assignee_id", "tickets", ["assignee_id"])
    op.create_index("ix_tickets_requester_id", "tickets", ["requester_id"])
    op.create_index("ix_tickets_priority_id", "tickets", ["priority_id"])
    op.create_index("ix_tickets_type_id", "tickets", ["type_id"])
    op.create_index("ix_tickets_sla_violated", "tickets", ["sla_violated"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])
    op.create_index("ix_tickets_updated_at", "tickets", ["updated_at"])

    # Составные индексы для типичных запросов агентов (department + status)
    op.create_index("ix_tickets_dept_status", "tickets", ["department_id", "status"])
    op.create_index("ix_tickets_assignee_status", "tickets", ["assignee_id", "status"])

    # Ticket history — часто фильтруется по ticket_id
    op.create_index("ix_ticket_history_ticket_id", "ticket_history", ["ticket_id"])

    # Notifications — фильтр по пользователю и статусу прочтения
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_user_is_read", "notifications", ["user_id", "is_read"])

    # Comments — по заявке
    op.create_index("ix_comments_ticket_id", "comments", ["ticket_id"])

    # Attachments — по заявке
    op.create_index("ix_attachments_ticket_id", "attachments", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_attachments_ticket_id", table_name="attachments")
    op.drop_index("ix_comments_ticket_id", table_name="comments")
    op.drop_index("ix_notifications_user_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_ticket_history_ticket_id", table_name="ticket_history")
    op.drop_index("ix_tickets_assignee_status", table_name="tickets")
    op.drop_index("ix_tickets_dept_status", table_name="tickets")
    op.drop_index("ix_tickets_updated_at", table_name="tickets")
    op.drop_index("ix_tickets_created_at", table_name="tickets")
    op.drop_index("ix_tickets_sla_violated", table_name="tickets")
    op.drop_index("ix_tickets_type_id", table_name="tickets")
    op.drop_index("ix_tickets_priority_id", table_name="tickets")
    op.drop_index("ix_tickets_requester_id", table_name="tickets")
    op.drop_index("ix_tickets_assignee_id", table_name="tickets")
    op.drop_index("ix_tickets_department_id", table_name="tickets")
    op.drop_index("ix_tickets_status", table_name="tickets")
