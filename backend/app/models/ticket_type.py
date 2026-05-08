from sqlalchemy import String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TicketType(Base):
    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    work_direction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    default_department: Mapped["Department | None"] = relationship(  # noqa: F821
        "Department", foreign_keys=[default_department_id]
    )
