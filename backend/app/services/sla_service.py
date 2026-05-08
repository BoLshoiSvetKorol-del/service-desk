from datetime import datetime, timedelta, timezone

WORK_START = 9   # 09:00
WORK_END = 18    # 18:00
WORK_DAYS = {0, 1, 2, 3, 4}  # Mon–Fri

REOPEN_WINDOW_HOURS = 72


def _is_workday(dt: datetime) -> bool:
    return dt.weekday() in WORK_DAYS


def _next_work_start(dt: datetime) -> datetime:
    """Следующий рабочий день 09:00."""
    next_day = dt.replace(hour=WORK_START, minute=0, second=0, microsecond=0) + timedelta(days=1)
    while not _is_workday(next_day):
        next_day += timedelta(days=1)
    return next_day


def calculate_deadline(start: datetime, sla_hours: int) -> datetime:
    """Добавить N рабочих часов к start, учитывая рабочее расписание пн-пт 09-18."""
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    current = start
    remaining = timedelta(hours=sla_hours)

    while remaining.total_seconds() > 0:
        if not _is_workday(current):
            current = _next_work_start(current)
            continue

        work_start = current.replace(hour=WORK_START, minute=0, second=0, microsecond=0)
        work_end = current.replace(hour=WORK_END, minute=0, second=0, microsecond=0)

        if current >= work_end:
            current = _next_work_start(current)
            continue

        if current < work_start:
            current = work_start

        available = work_end - current
        if remaining <= available:
            current = current + remaining
            remaining = timedelta(0)
        else:
            remaining -= available
            current = _next_work_start(current)

    return current


def pause_sla(ticket) -> None:
    """Поставить SLA на паузу (переход в waiting_info)."""
    ticket.sla_paused_at = datetime.now(timezone.utc)


def resume_sla(ticket) -> None:
    """Возобновить SLA (выход из waiting_info), добавить паузу к дедлайну."""
    if ticket.sla_paused_at is None:
        return

    now = datetime.now(timezone.utc)
    paused_at = ticket.sla_paused_at
    if paused_at.tzinfo is None:
        paused_at = paused_at.replace(tzinfo=timezone.utc)

    pause_minutes = int((now - paused_at).total_seconds() / 60)
    ticket.sla_extra_minutes = (ticket.sla_extra_minutes or 0) + pause_minutes

    if ticket.sla_deadline:
        deadline = ticket.sla_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        ticket.sla_deadline = deadline + timedelta(minutes=pause_minutes)

    ticket.sla_paused_at = None


def check_sla_violated(ticket) -> bool:
    """True если дедлайн пропущен и заявка ещё активна."""
    if ticket.status in ("resolved", "cancelled"):
        return False
    if not ticket.sla_deadline:
        return False
    deadline = ticket.sla_deadline
    now = datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return now > deadline and ticket.sla_paused_at is None
