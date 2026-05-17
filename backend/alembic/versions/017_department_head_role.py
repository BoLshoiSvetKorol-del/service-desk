"""add department_head role and cancellation_reason to ticket history

Revision ID: 017
Revises: 016
Create Date: 2026-05-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new value to the userrole enum in PostgreSQL
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'department_head'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values without recreating the type
    # This downgrade is intentionally a no-op
    pass
