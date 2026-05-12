"""routing rules for auto ticket assignment

Revision ID: 015
Revises: 014
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routing_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("keywords", sa.Text, nullable=True),
        sa.Column("ticket_type_id", sa.Integer,
                  sa.ForeignKey("ticket_types.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", sa.Integer,
                  sa.ForeignKey("departments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignee_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_routing_rules_priority", "routing_rules", ["priority"])
    op.create_index("ix_routing_rules_is_active", "routing_rules", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_routing_rules_is_active", table_name="routing_rules")
    op.drop_index("ix_routing_rules_priority", table_name="routing_rules")
    op.drop_table("routing_rules")
