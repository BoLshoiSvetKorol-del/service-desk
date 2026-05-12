"""user_contact_fields

Revision ID: 014
Revises: 013
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("contact_info", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "contact_info")
    op.drop_column("users", "phone")
