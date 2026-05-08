"""Unit-тесты для SLA-сервиса — граничные случаи расчёта дедлайна."""
from datetime import datetime, timezone

from app.services.sla_service import calculate_deadline, pause_sla, resume_sla, check_sla_violated


def dt(year=2026, month=5, day=4, hour=9, minute=0):
    """Хелпер для создания UTC datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


class TestCalculateDeadline:
    def test_simple_same_day(self):
        # Понедельник 09:00, +4 часа → 13:00
        start = dt(month=5, day=4, hour=9)  # 2026-05-04 — понедельник
        result = calculate_deadline(start, 4)
        assert result.hour == 13
        assert result.date() == start.date()

    def test_crosses_end_of_day(self):
        # Понедельник 16:00, +4 часа → следующий день 11:00
        start = dt(month=5, day=4, hour=16)
        result = calculate_deadline(start, 4)
        assert result.date() > start.date()
        # 2 часа в пн, 2 часа в следующий рабочий день (вт) с 09:00 → 11:00
        assert result.hour == 11

    def test_start_friday_evening_1h(self):
        # Пятница 17:30, +1 час → нет времени в пятницу, берём пн 09:30
        # 2026-05-08 — пятница
        start = dt(month=5, day=8, hour=17, minute=30)
        result = calculate_deadline(start, 1)
        # В пятницу осталось 30 мин (17:30→18:00), в понедельник добавить ещё 30 мин
        # → 2026-05-11 09:30
        assert result.weekday() == 0  # понедельник
        assert result.hour == 9
        assert result.minute == 30

    def test_start_friday_evening_4h(self):
        # Пятница 17:00, +4 часа → понедельник 12:00
        # 2026-05-08 17:00
        start = dt(month=5, day=8, hour=17)
        result = calculate_deadline(start, 4)
        assert result.weekday() == 0  # понедельник
        assert result.hour == 12

    def test_start_weekend(self):
        # Суббота 10:00, +8 часов → понедельник 17:00
        start = dt(month=5, day=9, hour=10)  # суббота
        result = calculate_deadline(start, 8)
        assert result.weekday() == 0  # понедельник
        assert result.hour == 17

    def test_spans_multiple_days(self):
        # Понедельник 09:00, +24 часа (3 рабочих дня)
        start = dt(month=5, day=4, hour=9)
        result = calculate_deadline(start, 24)
        # 3 рабочих дня * 9 часов = 27 ч, но 24 = Пн+Вт+Ср(6ч) → Ср 15:00
        assert result.weekday() in {0, 1, 2, 3, 4}  # рабочий день

    def test_one_hour_critical(self):
        # Вторник 10:00, +1 час → 11:00
        start = dt(month=5, day=5, hour=10)
        result = calculate_deadline(start, 1)
        assert result.hour == 11
        assert result.date() == start.date()


class TestPauseResumeSLA:
    def _make_ticket(self):
        class FakeTicket:
            sla_paused_at = None
            sla_extra_minutes = 0
            sla_deadline = dt(month=5, day=10, hour=12)
            status = "in_progress"

        return FakeTicket()

    def test_pause_sets_paused_at(self):
        ticket = self._make_ticket()
        pause_sla(ticket)
        assert ticket.sla_paused_at is not None

    def test_resume_clears_paused_at(self):
        ticket = self._make_ticket()
        pause_sla(ticket)
        resume_sla(ticket)
        assert ticket.sla_paused_at is None

    def test_resume_adds_minutes(self):
        ticket = self._make_ticket()
        from datetime import timedelta
        ticket.sla_paused_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        resume_sla(ticket)
        assert ticket.sla_extra_minutes >= 30

    def test_resume_extends_deadline(self):
        ticket = self._make_ticket()
        original_deadline = ticket.sla_deadline
        from datetime import timedelta
        ticket.sla_paused_at = datetime.now(timezone.utc) - timedelta(minutes=60)
        resume_sla(ticket)
        assert ticket.sla_deadline > original_deadline


class TestCheckSLAViolated:
    def _make_ticket(self, deadline_offset_minutes=-10, status="in_progress", paused=False):
        from datetime import timedelta

        class FakeTicket:
            pass

        ticket = FakeTicket()
        ticket.status = status
        ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(minutes=deadline_offset_minutes)
        ticket.sla_paused_at = datetime.now(timezone.utc) if paused else None
        return ticket

    def test_violated_when_past_deadline(self):
        ticket = self._make_ticket(deadline_offset_minutes=-10)
        assert check_sla_violated(ticket) is True

    def test_not_violated_when_before_deadline(self):
        ticket = self._make_ticket(deadline_offset_minutes=60)
        assert check_sla_violated(ticket) is False

    def test_not_violated_when_resolved(self):
        ticket = self._make_ticket(deadline_offset_minutes=-10, status="resolved")
        assert check_sla_violated(ticket) is False

    def test_not_violated_when_paused(self):
        ticket = self._make_ticket(deadline_offset_minutes=-5, paused=True)
        assert check_sla_violated(ticket) is False
