from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.priority import Priority, PriorityLevel

PRIORITY_SEED = [
    {"level": PriorityLevel.low,      "name": "Низкий",    "sla_hours": 24, "color_hex": "#8c8c8c"},
    {"level": PriorityLevel.normal,   "name": "Нормальный","sla_hours": 8,  "color_hex": "#1677ff"},
    {"level": PriorityLevel.high,     "name": "Высокий",   "sla_hours": 4,  "color_hex": "#fa8c16"},
    {"level": PriorityLevel.critical, "name": "Критичный", "sla_hours": 1,  "color_hex": "#f5222d"},
]


async def seed_priorities(db: AsyncSession) -> None:
    for p in PRIORITY_SEED:
        existing = await db.scalar(select(Priority).where(Priority.level == p["level"]))
        if not existing:
            db.add(Priority(**p))
    await db.commit()
