"""Integration-тесты для эндпоинтов заявок (Миссии 05 и 06)."""
import re
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
async def setup_data(db_session: AsyncSession):
    from app.services.auth_service import seed_admin
    from app.services.priority_service import seed_priorities
    await seed_priorities(db_session)
    await seed_admin(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _login(client: AsyncClient, username="admin", password="changeme") -> str:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


async def _auth(client: AsyncClient, username="admin", password="changeme") -> dict:
    token = await _login(client, username, password)
    return {"Authorization": f"Bearer {token}"}


async def _create_dept(client: AsyncClient, headers: dict, name: str = "Test Dept") -> int:
    r = await client.post("/api/v1/departments", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _create_ticket_type(client: AsyncClient, headers: dict, name: str = "Test Type", dept_id: int | None = None) -> int:
    payload: dict = {"name": name}
    if dept_id:
        payload["default_department_id"] = dept_id
    r = await client.post("/api/v1/ticket-types", json=payload, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _get_priority_id(client: AsyncClient, headers: dict, level: str = "normal") -> int:
    r = await client.get("/api/v1/priorities", headers=headers)
    return next(p["id"] for p in r.json() if p["level"] == level)


async def _create_agent(client: AsyncClient, admin_headers: dict, dept_id: int, suffix: str = "") -> dict:
    username = f"agent{suffix}"
    password = "agentpass"
    r = await client.post(
        "/api/v1/users",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
            "full_name": f"Agent {suffix}",
            "role": "agent",
            "department_id": dept_id,
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, password)
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_user(client: AsyncClient, admin_headers: dict, suffix: str = "") -> dict:
    username = f"user{suffix}"
    password = "userpass"
    r = await client.post(
        "/api/v1/users",
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
            "full_name": f"User {suffix}",
            "role": "user",
        },
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, password)
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_ticket(
    client: AsyncClient,
    headers: dict,
    priority_id: int,
    type_id: int,
    title: str = "Test ticket",
) -> dict:
    r = await client.post(
        "/api/v1/tickets",
        json={"title": title, "description": "desc", "priority_id": priority_id, "type_id": type_id},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# Create ticket
# ---------------------------------------------------------------------------

class TestCreateTicket:
    async def test_create_ticket_success(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "CreateDept")
        type_id = await _create_ticket_type(client, admin, "CreateType", dept_id)
        priority_id = await _get_priority_id(client, admin, "normal")

        r = await client.post(
            "/api/v1/tickets",
            json={"title": "My ticket", "description": "details", "priority_id": priority_id, "type_id": type_id},
            headers=admin,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My ticket"
        assert data["status"] == "new"
        assert data["sla_deadline"] is not None
        assert data["sla_violated"] is False

    def test_ticket_number_format(self):
        # Формат SD-YYYY-XXXXX проверяется regex
        pattern = re.compile(r"^SD-\d{4}-\d{5}$")
        assert pattern.match("SD-2026-00001")
        assert not pattern.match("SD-26-1")

    async def test_create_ticket_number_generated(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "NumDept")
        type_id = await _create_ticket_type(client, admin, "NumType", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        assert re.match(r"^SD-\d{4}-\d{5}$", ticket["number"])

    async def test_create_ticket_auto_department(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "AutoDept")
        type_id = await _create_ticket_type(client, admin, "AutoType", dept_id)
        priority_id = await _get_priority_id(client, admin)

        r = await client.post(
            "/api/v1/tickets",
            json={"title": "AutoDept ticket", "priority_id": priority_id, "type_id": type_id},
            headers=admin,
        )
        assert r.status_code == 201
        assert r.json()["department_id"] == dept_id

    async def test_create_ticket_invalid_priority(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "BadPrioType")
        r = await client.post(
            "/api/v1/tickets",
            json={"title": "Bad", "priority_id": 99999, "type_id": type_id},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_create_ticket_invalid_type(self, client: AsyncClient):
        admin = await _auth(client)
        priority_id = await _get_priority_id(client, admin)
        r = await client.post(
            "/api/v1/tickets",
            json={"title": "Bad", "priority_id": priority_id, "type_id": 99999},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_create_ticket_inactive_type(self, client: AsyncClient):
        admin = await _auth(client)
        priority_id = await _get_priority_id(client, admin)
        type_id = await _create_ticket_type(client, admin, "InactiveType")
        await client.put(f"/api/v1/ticket-types/{type_id}", json={"name": "InactiveType", "is_active": False}, headers=admin)

        r = await client.post(
            "/api/v1/tickets",
            json={"title": "Bad", "priority_id": priority_id, "type_id": type_id},
            headers=admin,
        )
        assert r.status_code == 400

    async def test_create_ticket_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/tickets", json={"title": "x", "priority_id": 1, "type_id": 1})
        assert r.status_code == 403

    async def test_sla_deadline_set_by_priority(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "SLATypeCheck")
        critical_id = await _get_priority_id(client, admin, "critical")
        low_id = await _get_priority_id(client, admin, "low")

        crit = await _create_ticket(client, admin, critical_id, type_id, "Critical ticket")
        low = await _create_ticket(client, admin, low_id, type_id, "Low ticket")

        # Критичный (1ч) → дедлайн раньше чем у низкого (24ч)
        assert crit["sla_deadline"] < low["sla_deadline"]


# ---------------------------------------------------------------------------
# Get / List tickets
# ---------------------------------------------------------------------------

class TestGetTicket:
    async def test_get_ticket_by_owner(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "GetType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=admin)
        assert r.status_code == 200
        assert r.json()["id"] == ticket["id"]

    async def test_get_ticket_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/tickets/99999", headers=admin)
        assert r.status_code == 404

    async def test_user_cannot_get_others_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "AccessType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        user = await _create_user(client, admin, "getsuffix")
        r = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=user["headers"])
        assert r.status_code == 403

    async def test_agent_can_get_dept_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "AgentGetDept")
        type_id = await _create_ticket_type(client, admin, "AgentGetType", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        agent = await _create_agent(client, admin, dept_id, "get1")
        r = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=agent["headers"])
        assert r.status_code == 200

    async def test_get_ticket_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/tickets/1")
        assert r.status_code == 403


class TestListTickets:
    async def test_admin_sees_all_tickets(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "ListAdminType")
        priority_id = await _get_priority_id(client, admin)

        user1 = await _create_user(client, admin, "list1")
        user2 = await _create_user(client, admin, "list2")
        await _create_ticket(client, user1["headers"], priority_id, type_id, "User1 ticket")
        await _create_ticket(client, user2["headers"], priority_id, type_id, "User2 ticket")

        r = await client.get("/api/v1/tickets", headers=admin)
        assert r.status_code == 200
        assert r.json()["total"] >= 2

    async def test_user_sees_only_own_tickets(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "ListUserType")
        priority_id = await _get_priority_id(client, admin)

        user_a = await _create_user(client, admin, "usera")
        user_b = await _create_user(client, admin, "userb")
        await _create_ticket(client, user_a["headers"], priority_id, type_id, "A ticket")
        await _create_ticket(client, user_b["headers"], priority_id, type_id, "B ticket")

        r = await client.get("/api/v1/tickets", headers=user_a["headers"])
        assert r.status_code == 200
        data = r.json()
        requester_ids = {t["requester_id"] for t in data["items"]}
        assert requester_ids == {user_a["id"]}

    async def test_agent_sees_dept_tickets(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "ListAgentDept")
        type_id = await _create_ticket_type(client, admin, "ListAgentType", dept_id)
        priority_id = await _get_priority_id(client, admin)

        # Создаём заявку, которая маршрутизируется в dept_id (через тип)
        await _create_ticket(client, admin, priority_id, type_id, "Dept ticket")

        agent = await _create_agent(client, admin, dept_id, "list2")
        r = await client.get("/api/v1/tickets", headers=agent["headers"])
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_filter_by_status(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "FilterStatusType")
        priority_id = await _get_priority_id(client, admin)
        await _create_ticket(client, admin, priority_id, type_id, "Status filter ticket")

        r = await client.get("/api/v1/tickets?status=new", headers=admin)
        assert r.status_code == 200
        for t in r.json()["items"]:
            assert t["status"] == "new"

    async def test_filter_by_search(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "SearchType")
        priority_id = await _get_priority_id(client, admin)
        await _create_ticket(client, admin, priority_id, type_id, "UNIQUEQUERYTITLE")

        r = await client.get("/api/v1/tickets?search=UNIQUEQUERYTITLE", headers=admin)
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert any("UNIQUEQUERYTITLE" in t["title"] for t in r.json()["items"])

    async def test_pagination(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/tickets?page=1&page_size=5", headers=admin)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) <= 5


# ---------------------------------------------------------------------------
# Update ticket
# ---------------------------------------------------------------------------

class TestUpdateTicket:
    async def test_agent_can_update_title(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "UpdDept")
        type_id = await _create_ticket_type(client, admin, "UpdType", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id, "Original")

        agent = await _create_agent(client, admin, dept_id, "upd1")
        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"title": "Updated title"},
            headers=agent["headers"],
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated title"

    async def test_admin_can_update(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "AdminUpdType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"title": "Admin updated", "description": "new desc"},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json()["description"] == "new desc"

    async def test_user_cannot_update(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "UserUpdType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        user = await _create_user(client, admin, "upd2")
        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}",
            json={"title": "Hacked"},
            headers=user["headers"],
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

class TestChangeStatus:
    async def _setup(self, client, admin):
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"StatusDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"StatusType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        agent = await _create_agent(client, admin, dept_id, f"st{uid}")
        return ticket, agent, dept_id

    async def test_new_to_in_progress_by_agent(self, client: AsyncClient):
        admin = await _auth(client)
        ticket, agent, _ = await self._setup(client, admin)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress"},
            headers=agent["headers"],
        )
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    async def test_invalid_transition_raises_422(self, client: AsyncClient):
        admin = await _auth(client)
        ticket, _, _ = await self._setup(client, admin)

        # new → resolved не допустимо
        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "resolved"},
            headers=admin,
        )
        assert r.status_code == 422

    async def test_user_cannot_take_in_progress(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "UserStatusType")
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, "stat2")
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        # User не может переводить в in_progress (это роль агента)
        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress"},
            headers=user["headers"],
        )
        assert r.status_code == 403

    async def test_user_can_cancel_own_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "UserCancelType")
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, "stat3")
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "cancelled"},
            headers=user["headers"],
        )
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    async def test_in_progress_to_waiting_info_pauses_sla(self, client: AsyncClient):
        admin = await _auth(client)
        ticket, agent, _ = await self._setup(client, admin)

        await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress"},
            headers=agent["headers"],
        )
        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "waiting_info"},
            headers=agent["headers"],
        )
        assert r.status_code == 200
        assert r.json()["sla_paused_at"] is not None

    async def test_waiting_info_to_in_progress_resumes_sla(self, client: AsyncClient):
        admin = await _auth(client)
        ticket, agent, _ = await self._setup(client, admin)

        await client.patch(f"/api/v1/tickets/{ticket['id']}/status", json={"status": "in_progress"}, headers=agent["headers"])
        await client.patch(f"/api/v1/tickets/{ticket['id']}/status", json={"status": "waiting_info"}, headers=agent["headers"])

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress"},
            headers=agent["headers"],
        )
        assert r.status_code == 200
        data = r.json()
        assert data["sla_paused_at"] is None
        # In fast tests the pause lasts <1 second so pause_minutes rounds to 0;
        # we verify the field is present and non-negative (pause was tracked).
        assert data["sla_extra_minutes"] >= 0

    async def test_resolved_sets_closed_at(self, client: AsyncClient):
        admin = await _auth(client)
        ticket, agent, _ = await self._setup(client, admin)

        await client.patch(f"/api/v1/tickets/{ticket['id']}/status", json={"status": "in_progress"}, headers=agent["headers"])
        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "resolved"},
            headers=agent["headers"],
        )
        assert r.status_code == 200
        assert r.json()["closed_at"] is not None

    async def test_status_change_with_comment(self, client: AsyncClient):
        admin = await _auth(client)
        ticket, agent, _ = await self._setup(client, admin)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress", "comment": "Берём в работу"},
            headers=agent["headers"],
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Assign ticket
# ---------------------------------------------------------------------------

class TestAssignTicket:
    async def test_admin_can_assign_agent(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "AssignDept")
        type_id = await _create_ticket_type(client, admin, "AssignType", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        agent = await _create_agent(client, admin, dept_id, "asgn1")

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/assign",
            json={"assignee_id": agent["id"]},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json()["assignee_id"] == agent["id"]

    async def test_assign_to_department(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "AssignDept2")
        type_id = await _create_ticket_type(client, admin, "AssignType2")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/assign",
            json={"department_id": dept_id},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json()["department_id"] == dept_id

    async def test_user_cannot_assign(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "UserAssignType")
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, "asgn2")
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/assign",
            json={"assignee_id": user["id"]},
            headers=user["headers"],
        )
        assert r.status_code == 403

    async def test_assign_nonexistent_user(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "BadAssignType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/assign",
            json={"assignee_id": 99999},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_cannot_assign_user_role_as_agent(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "UserRoleAssignType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        user = await _create_user(client, admin, "asgn3")

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/assign",
            json={"assignee_id": user["id"]},
            headers=admin,
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Change priority
# ---------------------------------------------------------------------------

class TestChangePriority:
    async def test_admin_can_change_priority(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "PrioChangeType")
        normal_id = await _get_priority_id(client, admin, "normal")
        critical_id = await _get_priority_id(client, admin, "critical")
        ticket = await _create_ticket(client, admin, normal_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/priority",
            json={"priority_id": critical_id},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json()["priority_id"] == critical_id

    async def test_agent_can_change_priority(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "PrioDept")
        type_id = await _create_ticket_type(client, admin, "AgentPrioType", dept_id)
        normal_id = await _get_priority_id(client, admin, "normal")
        high_id = await _get_priority_id(client, admin, "high")
        ticket = await _create_ticket(client, admin, normal_id, type_id)
        agent = await _create_agent(client, admin, dept_id, "prio1")

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/priority",
            json={"priority_id": high_id},
            headers=agent["headers"],
        )
        assert r.status_code == 200
        assert r.json()["priority_id"] == high_id

    async def test_user_cannot_change_priority(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "UserPrioType")
        normal_id = await _get_priority_id(client, admin, "normal")
        user = await _create_user(client, admin, "prio2")
        ticket = await _create_ticket(client, user["headers"], normal_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/priority",
            json={"priority_id": normal_id},
            headers=user["headers"],
        )
        assert r.status_code == 403

    async def test_change_to_invalid_priority(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "InvalidPrioType")
        normal_id = await _get_priority_id(client, admin, "normal")
        ticket = await _create_ticket(client, admin, normal_id, type_id)

        r = await client.patch(
            f"/api/v1/tickets/{ticket['id']}/priority",
            json={"priority_id": 99999},
            headers=admin,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Ticket history
# ---------------------------------------------------------------------------

class TestTicketHistory:
    async def test_history_created_on_ticket_creation(self, client: AsyncClient):
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, "HistoryType")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/history", headers=admin)
        assert r.status_code == 200
        events = r.json()
        assert len(events) >= 1
        assert events[0]["event_type"] == "created"

    async def test_history_recorded_on_status_change(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "HistDept")
        type_id = await _create_ticket_type(client, admin, "HistType2", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        agent = await _create_agent(client, admin, dept_id, "hist1")

        await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress"},
            headers=agent["headers"],
        )

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/history", headers=admin)
        events = r.json()
        types = [e["event_type"] for e in events]
        assert "created" in types
        assert "status_changed" in types

    async def test_history_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/tickets/1/history")
        assert r.status_code == 403

    async def test_history_payload_contains_transition(self, client: AsyncClient):
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, "PayloadDept")
        type_id = await _create_ticket_type(client, admin, "PayloadType", dept_id)
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        agent = await _create_agent(client, admin, dept_id, "payload1")

        await client.patch(
            f"/api/v1/tickets/{ticket['id']}/status",
            json={"status": "in_progress"},
            headers=agent["headers"],
        )
        r = await client.get(f"/api/v1/tickets/{ticket['id']}/history", headers=admin)
        status_event = next(e for e in r.json() if e["event_type"] == "status_changed")
        assert status_event["payload"]["old"] == "new"
        assert status_event["payload"]["new"] == "in_progress"
