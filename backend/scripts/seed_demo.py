"""
Seed script: fills the DB with demo data for testing.
Run: docker exec projectx-backend-1 python scripts/seed_demo.py
"""
import asyncio
import sys
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://servicedesk:servicedesk@postgres:5432/servicedesk")
os.environ.setdefault("SECRET_KEY", "changeme-secret-key-32chars-minimum!")

from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

sys.path.insert(0, "/app")

DATABASE_URL = os.environ["DATABASE_URL"]


async def main():
    engine = create_async_engine(DATABASE_URL)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        from app.models import (
            Department, User, Priority, TicketType, Ticket, TicketHistory,
            Comment, Tag,
        )
        from app.models.ticket import TicketStatus
        from app.models.user import UserRole
        from app.models.ticket_note import TicketNote
        from app.utils.security import hash_password
        from app.utils.ticket_number import generate_ticket_number

        # ── Departments ──────────────────────────────────────────────────────
        depts_data = [
            ("ИТ-поддержка", "Первая и вторая линия ИТ-поддержки"),
            ("HR", "Кадровый отдел"),
            ("Бухгалтерия", "Финансовый учёт и расчёты"),
            ("АХО", "Административно-хозяйственный отдел"),
        ]
        depts = {}
        for name, desc in depts_data:
            existing = await db.scalar(select(Department).where(Department.name == name))
            if not existing:
                d = Department(name=name, description=desc)
                db.add(d)
                await db.flush()
                depts[name] = d
            else:
                depts[name] = existing
        print(f"Departments: {list(depts.keys())}")

        # ── Priorities ───────────────────────────────────────────────────────
        prios = {}
        result = await db.execute(select(Priority))
        for p in result.scalars().all():
            prios[p.level] = p
        print(f"Priorities found: {list(prios.keys())}")

        # ── Ticket Types ─────────────────────────────────────────────────────
        types_data = [
            ("Настройка оборудования", "hardware", depts["ИТ-поддержка"].id),
            ("Проблема с ПО", "software", depts["ИТ-поддержка"].id),
            ("Доступ к системе", "access", depts["ИТ-поддержка"].id),
            ("Кадровый вопрос", "hr_general", depts["HR"].id),
            ("Документы / справки", "hr_docs", depts["HR"].id),
            ("Хозяйственная нужда", "facilities", depts["АХО"].id),
        ]
        ttypes = {}
        for name, svc, dept_id in types_data:
            existing = await db.scalar(select(TicketType).where(TicketType.name == name))
            if not existing:
                tt = TicketType(name=name, service_type=svc, default_department_id=dept_id, is_active=True)
                db.add(tt)
                await db.flush()
                ttypes[name] = tt
            else:
                ttypes[name] = existing
        print(f"Ticket types: {list(ttypes.keys())}")

        # ── Tags ─────────────────────────────────────────────────────────────
        tags_data = [
            ("срочно", "#f5222d"),
            ("баг", "#fa541c"),
            ("запрос", "#1677ff"),
            ("оборудование", "#722ed1"),
            ("ПО", "#13c2c2"),
            ("VPN", "#2f54eb"),
            ("принтер", "#eb2f96"),
            ("почта", "#faad14"),
            ("1С", "#52c41a"),
            ("новый сотрудник", "#08979c"),
            ("увольнение", "#cf1322"),
            ("удалённая работа", "#7cb305"),
        ]
        tags = {}
        for name, color in tags_data:
            existing = await db.scalar(select(Tag).where(Tag.name == name))
            if not existing:
                t = Tag(name=name, color_hex=color)
                db.add(t)
                await db.flush()
                tags[name] = t
            else:
                tags[name] = existing
        print(f"Tags: {list(tags.keys())}")

        # ── Agents ───────────────────────────────────────────────────────────
        agents_data = [
            ("ivanov", "Иванов Алексей", "ivanov@company.ru", depts["ИТ-поддержка"].id),
            ("petrov", "Петров Сергей", "petrov@company.ru", depts["ИТ-поддержка"].id),
            ("sidorova", "Сидорова Мария", "sidorova@company.ru", depts["HR"].id),
            ("kozlov", "Козлов Дмитрий", "kozlov@company.ru", depts["АХО"].id),
        ]
        agents = {}
        for username, full_name, email, dept_id in agents_data:
            existing = await db.scalar(select(User).where(User.username == username))
            if not existing:
                u = User(
                    username=username, full_name=full_name, email=email,
                    password_hash=hash_password("pass123"),
                    role=UserRole.agent, department_id=dept_id, is_active=True,
                )
                db.add(u)
                await db.flush()
                agents[username] = u
            else:
                agents[username] = existing
        print(f"Agents: {list(agents.keys())}")

        # ── Users (regular) ──────────────────────────────────────────────────
        users_data = [
            ("smirnov", "Смирнов Игорь", "smirnov@company.ru"),
            ("volkova", "Волкова Елена", "volkova@company.ru"),
            ("morozov", "Морозов Павел", "morozov@company.ru"),
            ("novikova", "Новикова Анна", "novikova@company.ru"),
            ("fedorov", "Фёдоров Кирилл", "fedorov@company.ru"),
            ("alekseeva", "Алексеева Юлия", "alekseeva@company.ru"),
            ("sokolov", "Соколов Андрей", "sokolov@company.ru"),
            ("mikhailova", "Михайлова Светлана", "mikhailova@company.ru"),
        ]
        users = {}
        for username, full_name, email in users_data:
            existing = await db.scalar(select(User).where(User.username == username))
            if not existing:
                u = User(
                    username=username, full_name=full_name, email=email,
                    password_hash=hash_password("pass123"),
                    role=UserRole.user, is_active=True,
                )
                db.add(u)
                await db.flush()
                users[username] = u
            else:
                users[username] = existing
        print(f"Users: {list(users.keys())}")

        await db.commit()

        # ── Tickets ──────────────────────────────────────────────────────────
        admin = await db.scalar(select(User).where(User.username == "admin"))

        tickets_data = [
            # (title, type_name, priority_level, requester, assignee, status, tags_list, comment)
            ("Не работает VPN с домашнего ПК", "Доступ к системе", "high",
             users["smirnov"], agents["ivanov"], TicketStatus.in_progress,
             ["VPN", "удалённая работа"],
             "Пробовали переустановить клиент, не помогло."),

            ("Замена картриджа в принтере 3 этаж", "Хозяйственная нужда", "normal",
             users["volkova"], agents["kozlov"], TicketStatus.resolved,
             ["принтер"],
             "Картридж заменён, принтер работает."),

            ("1С не открывается после обновления", "Проблема с ПО", "critical",
             users["morozov"], agents["petrov"], TicketStatus.in_progress,
             ["1С", "баг", "срочно"],
             "Ошибка при запуске: 'Недопустимая операция для данного типа объекта'."),

            ("Нужен доступ к папке HR на сервере", "Доступ к системе", "normal",
             users["novikova"], agents["ivanov"], TicketStatus.new,
             ["запрос"],
             None),

            ("Не приходят письма в Outlook", "Проблема с ПО", "high",
             users["fedorov"], agents["petrov"], TicketStatus.waiting_info,
             ["почта", "ПО"],
             "Уточните: Outlook desktop или web-версия?"),

            ("Оформление на работу нового сотрудника", "Кадровый вопрос", "normal",
             admin, agents["sidorova"], TicketStatus.in_progress,
             ["новый сотрудник", "HR"],
             "Выход 12 июня, отдел ИТ."),

            ("Не работает сканер в бухгалтерии", "Настройка оборудования", "normal",
             users["alekseeva"], agents["ivanov"], TicketStatus.resolved,
             ["оборудование"],
             "Переустановлен драйвер, сканер работает."),

            ("Запрос справки 2-НДФЛ", "Документы / справки", "low",
             users["sokolov"], agents["sidorova"], TicketStatus.new,
             ["запрос"],
             None),

            ("Ноутбук не заряжается", "Настройка оборудования", "high",
             users["mikhailova"], agents["ivanov"], TicketStatus.in_progress,
             ["оборудование", "срочно"],
             "Проверили блок питания — работает. Проблема в разъёме ноутбука."),

            ("Заблокирована учётная запись AD", "Доступ к системе", "high",
             users["smirnov"], agents["petrov"], TicketStatus.resolved,
             ["запрос"],
             "Учётная запись разблокирована, причина — 3 неверных попытки входа."),

            ("Увольнение: отзыв доступов", "Кадровый вопрос", "normal",
             admin, agents["sidorova"], TicketStatus.resolved,
             ["увольнение"],
             "Все доступы отозваны, оборудование возвращено."),

            ("Обновление Windows зависает на 45%", "Проблема с ПО", "normal",
             users["morozov"], agents["petrov"], TicketStatus.cancelled,
             ["ПО"],
             "Проблема устранена сама после перезагрузки."),

            ("Нет интернета на рабочем месте", "Настройка оборудования", "high",
             users["volkova"], agents["ivanov"], TicketStatus.resolved,
             ["срочно"],
             "Кабель был перегнут. Заменили патч-корд."),

            ("Установить Microsoft Office", "Проблема с ПО", "normal",
             users["fedorov"], agents["petrov"], TicketStatus.new,
             ["ПО", "запрос"],
             None),

            ("Нужен второй монитор для работы", "Хозяйственная нужда", "low",
             users["novikova"], agents["kozlov"], TicketStatus.new,
             ["запрос", "удалённая работа"],
             None),
        ]

        now = datetime.now(timezone.utc)
        created_tickets = []

        OPEN_STATUSES = {TicketStatus.new, TicketStatus.in_progress, TicketStatus.waiting_info}

        for i, (title, type_name, prio_level, requester, assignee, status, tag_names, comment_text) in enumerate(tickets_data):
            # check if already exists
            existing = await db.scalar(select(Ticket).where(Ticket.title == title))
            if existing:
                created_tickets.append(existing)
                continue

            tt = ttypes[type_name]
            prio = prios.get(prio_level)
            if not prio:
                continue

            number = await generate_ticket_number(db)

            from app.services.sla_service import calculate_deadline

            if status in OPEN_STATUSES:
                # Recent created_at so SLA deadline is in the future
                created_at = now - timedelta(hours=i + 1)
                sla_deadline = calculate_deadline(now, prio.sla_hours * 2)
                # Only a couple of open tickets are explicitly violated for demo
                sla_violated = (status == TicketStatus.in_progress and i == 0)
            else:
                # Historical dates for closed tickets
                created_at = now - timedelta(days=30 - i * 2, hours=i * 3)
                sla_deadline = calculate_deadline(created_at, prio.sla_hours)
                sla_violated = False

            ticket = Ticket(
                number=number,
                title=title,
                description=f"Описание заявки: {title}. Пожалуйста, помогите решить данный вопрос.",
                status=status,
                priority_id=prio.id,
                type_id=tt.id,
                requester_id=requester.id,
                assignee_id=assignee.id if assignee else None,
                department_id=tt.default_department_id,
                sla_deadline=sla_deadline,
                sla_extra_minutes=0,
                sla_violated=sla_violated,
                created_at=created_at,
                updated_at=created_at,
            )
            if status in (TicketStatus.resolved, TicketStatus.cancelled):
                ticket.closed_at = created_at + timedelta(hours=prio.sla_hours * 0.8)

            db.add(ticket)
            await db.flush()

            # tags — insert directly to avoid lazy-load in async context
            for tag_name in tag_names:
                if tag_name in tags:
                    await db.execute(
                        text("INSERT INTO ticket_tags (ticket_id, tag_id) VALUES (:tid, :gid) ON CONFLICT DO NOTHING"),
                        {"tid": ticket.id, "gid": tags[tag_name].id},
                    )

            # history
            db.add(TicketHistory(
                ticket_id=ticket.id, user_id=requester.id,
                event_type="created",
                payload={"title": title},
                created_at=created_at,
            ))
            if assignee:
                db.add(TicketHistory(
                    ticket_id=ticket.id, user_id=admin.id if admin else None,
                    event_type="assigned",
                    payload={"new_assignee_id": assignee.id},
                    created_at=created_at + timedelta(minutes=30),
                ))
            if status != TicketStatus.new:
                db.add(TicketHistory(
                    ticket_id=ticket.id, user_id=assignee.id if assignee else None,
                    event_type="status_changed",
                    payload={"old": "new", "new": status.value},
                    created_at=created_at + timedelta(hours=1),
                ))

            # comment
            if comment_text and assignee:
                db.add(Comment(
                    ticket_id=ticket.id,
                    author_id=assignee.id,
                    body=comment_text,
                    is_internal=False,
                    created_at=created_at + timedelta(hours=2),
                    updated_at=created_at + timedelta(hours=2),
                ))

            # internal comment from agent
            if assignee and i % 3 == 0:
                db.add(Comment(
                    ticket_id=ticket.id,
                    author_id=assignee.id,
                    body=f"[Внутренняя заметка] Заявка принята в работу. Ориентировочное время решения: {prio.sla_hours} ч.",
                    is_internal=True,
                    created_at=created_at + timedelta(hours=1),
                    updated_at=created_at + timedelta(hours=1),
                ))

            created_tickets.append(ticket)

        await db.commit()
        print(f"Created {len(created_tickets)} tickets")

        # ── Agent notes ──────────────────────────────────────────────────────
        if created_tickets:
            for ticket in created_tickets[:5]:
                agent_user = agents.get("ivanov") or agents.get("petrov")
                if not agent_user:
                    continue
                existing_note = await db.scalar(
                    select(TicketNote).where(
                        TicketNote.ticket_id == ticket.id,
                        TicketNote.author_id == agent_user.id,
                    )
                )
                if not existing_note:
                    db.add(TicketNote(
                        ticket_id=ticket.id,
                        author_id=agent_user.id,
                        body="Связался с пользователем, ждём обратную связь.",
                    ))
            await db.commit()
            print("Agent notes created")

    print("\n✅ Seed complete!")
    print("\n=== Учётные данные ===")
    print("Администратор: admin / changeme")
    print("Агенты (пароль: pass123):")
    print("  ivanov  — ИТ-поддержка")
    print("  petrov  — ИТ-поддержка")
    print("  sidorova — HR")
    print("  kozlov  — АХО")
    print("Пользователи (пароль: pass123):")
    print("  smirnov, volkova, morozov, novikova, fedorov, alekseeva, sokolov, mikhailova")


if __name__ == "__main__":
    asyncio.run(main())
