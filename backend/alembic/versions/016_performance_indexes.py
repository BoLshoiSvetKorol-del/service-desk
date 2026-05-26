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
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_status ON tickets (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_department_id ON tickets (department_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_assignee_id ON tickets (assignee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_requester_id ON tickets (requester_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_priority_id ON tickets (priority_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_type_id ON tickets (type_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_sla_violated ON tickets (sla_violated)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_created_at ON tickets (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_updated_at ON tickets (updated_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_dept_status ON tickets (department_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tickets_assignee_status ON tickets (assignee_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ticket_history_ticket_id ON ticket_history (ticket_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_is_read ON notifications (user_id, is_read)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_ticket_id ON comments (ticket_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attachments_ticket_id ON attachments (ticket_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_attachments_ticket_id")
    op.execute("DROP INDEX IF EXISTS ix_comments_ticket_id")
    op.execute("DROP INDEX IF EXISTS ix_notifications_user_is_read")
    op.execute("DROP INDEX IF EXISTS ix_notifications_user_id")
    op.execute("DROP INDEX IF EXISTS ix_ticket_history_ticket_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_assignee_status")
    op.execute("DROP INDEX IF EXISTS ix_tickets_dept_status")
    op.execute("DROP INDEX IF EXISTS ix_tickets_updated_at")
    op.execute("DROP INDEX IF EXISTS ix_tickets_created_at")
    op.execute("DROP INDEX IF EXISTS ix_tickets_sla_violated")
    op.execute("DROP INDEX IF EXISTS ix_tickets_type_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_priority_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_requester_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_assignee_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_department_id")
    op.execute("DROP INDEX IF EXISTS ix_tickets_status")
