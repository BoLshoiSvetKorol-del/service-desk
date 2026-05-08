import enum
from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PriorityLevel(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class Priority(Base):
    __tablename__ = "priorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[PriorityLevel] = mapped_column(
        Enum(PriorityLevel, name="prioritylevel", create_type=True),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
