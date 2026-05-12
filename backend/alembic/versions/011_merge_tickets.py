"""merge tickets

Revision ID: 011
Revises: 010
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'merged' to ticketstatus enum
    op.execute("ALTER TYPE ticketstatus ADD VALUE IF NOT EXISTS 'merged'")

    # Add merged_into_id column
    op.add_column(
        "tickets",
        sa.Column(
            "merged_into_id",
            sa.Integer,
            sa.ForeignKey("tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_tickets_merged_into_id", "tickets", ["merged_into_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_merged_into_id", table_name="tickets")
    op.drop_column("tickets", "merged_into_id")
    # Note: PostgreSQL doesn't support removing enum values easily
