"""reference_data

Revision ID: 004
Revises: 003
Create Date: 2026-05-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "priorities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("low", "normal", "high", "critical", name="prioritylevel"),
            nullable=False,
        ),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=False),
        sa.Column("color_hex", sa.String(7), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("level", name="uq_priorities_level"),
    )

    op.create_table(
        "ticket_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("service_type", sa.String(255), nullable=True),
        sa.Column("work_direction", sa.String(255), nullable=True),
        sa.Column("default_department_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["default_department_id"], ["departments.id"],
            name="fk_ticket_types_default_department",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_ticket_types_name"),
    )


def downgrade() -> None:
    op.drop_table("ticket_types")
    op.drop_table("priorities")
    op.execute("DROP TYPE IF EXISTS prioritylevel")
