from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def generate_ticket_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    result = await db.execute(
        text("""
            INSERT INTO ticket_number_seq (year, last_number)
            VALUES (:year, 1)
            ON CONFLICT (year) DO UPDATE
                SET last_number = ticket_number_seq.last_number + 1
            RETURNING last_number
        """),
        {"year": year},
    )
    seq_num = result.scalar()
    return f"SD-{year}-{seq_num:05d}"
