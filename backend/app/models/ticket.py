import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class TicketStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    waiting_info = "waiting_info"
    resolved = "resolved"
    cancelled = "cancelled"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticketstatus", create_type=True),
        nullable=False,
        default=TicketStatus.new,
    )

    priority_id: Mapped[int] = mapped_column(Integer, ForeignKey("priorities.id"), nullable=False)
    type_id: Mapped[int] = mapped_column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    requester_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_extra_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sla_violated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    priority: Mapped["Priority"] = relationship("Priority", foreign_keys=[priority_id])  # noqa: F821
    ticket_type: Mapped["TicketType"] = relationship("TicketType", foreign_keys=[type_id])  # noqa: F821
    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id])  # noqa: F821
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_id])  # noqa: F821
    department: Mapped["Department | None"] = relationship("Department", foreign_keys=[department_id])  # noqa: F821
    history: Mapped[list["TicketHistory"]] = relationship(  # noqa: F821
        "TicketHistory", back_populates="ticket", order_by="TicketHistory.created_at"
    )
