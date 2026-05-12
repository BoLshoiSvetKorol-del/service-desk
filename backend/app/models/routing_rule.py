from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Comma-separated keywords; match ANY keyword in title+description (case-insensitive)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional: rule applies only when ticket matches this type
    ticket_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ticket_types.id", ondelete="SET NULL"), nullable=True
    )
    # Target department (required output of the rule)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    # Optional: auto-assign to a specific agent
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Lower value = evaluated first
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    department: Mapped["Department"] = relationship("Department", foreign_keys=[department_id], lazy="selectin")  # noqa: F821
    ticket_type: Mapped["TicketType | None"] = relationship("TicketType", foreign_keys=[ticket_type_id], lazy="selectin")  # noqa: F821
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_id], lazy="selectin")  # noqa: F821
