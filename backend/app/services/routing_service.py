from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.routing_rule import RoutingRule


async def find_matching_rule(
    db: AsyncSession,
    title: str,
    description: str | None,
    type_id: int | None,
) -> RoutingRule | None:
    """Return the first active rule that matches the ticket, or None.

    Rules are evaluated in ascending `priority` order (lower = first).
    Within the same priority, lower `id` wins (insertion order).

    A rule matches when ALL its conditions are satisfied:
    - If ticket_type_id is set: the ticket's type must match.
    - If keywords is set: at least one keyword must appear in title + description.
    """
    result = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.is_active == True)  # noqa: E712
        .order_by(RoutingRule.priority.asc(), RoutingRule.id.asc())
    )
    rules = result.scalars().all()

    text = f"{title} {description or ''}".lower()

    for rule in rules:
        if rule.ticket_type_id is not None and rule.ticket_type_id != type_id:
            continue

        if rule.keywords:
            keywords = [k.strip().lower() for k in rule.keywords.split(",") if k.strip()]
            if keywords and not any(kw in text for kw in keywords):
                continue

        return rule

    return None
