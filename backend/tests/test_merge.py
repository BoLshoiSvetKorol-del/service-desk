"""Integration tests for ticket merge (Mission 15)."""
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
# helpers
# ---------------------------------------------------------------------------

async def _login(client: AsyncClient, username="admin", password="changeme") -> str:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def _auth(client: AsyncClient, username="admin", password="changeme") -> dict:
    token = await _login(client, username, password)
    return {"Authorization": f"Bearer {token}"}


async def _create_dept(client: AsyncClient, headers: dict, name: str) -> int:
    r = await client.post("/api/v1/departments", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _create_ticket_type(client: AsyncClient, headers: dict, name: str, dept_id: int | None = None) -> int:
    payload: dict = {"name": name}
    if dept_id:
        payload["default_department_id"] = dept_id
    r = await client.post("/api/v1/ticket-types", json=payload, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _get_priority_id(client: AsyncClient, headers: dict, level: str = "normal") -> int:
    r = await client.get("/api/v1/priorities", headers=headers)
    return next(p["id"] for p in r.json() if p["level"] == level)


async def _create_user(client: AsyncClient, admin_headers: dict, suffix: str = "") -> dict:
    username = f"muser{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"MUser {suffix}", "role": "user"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_agent(client: AsyncClient, admin_headers: dict, dept_id: int, suffix: str = "") -> dict:
    username = f"magent{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"MAgent {suffix}", "role": "agent", "department_id": dept_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _make_ticket(client: AsyncClient, headers: dict, title: str, type_id: int, priority_id: int) -> dict:
    r = await client.post(
        "/api/v1/tickets",
        json={"title": title, "priority_id": priority_id, "type_id": type_id},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# POST /{id}/merge
# ---------------------------------------------------------------------------

class TestMergeTicket:
    async def test_agent_can_merge(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, f"MergeDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"MType{uid}", dept_id)
        prio_id = await _get_priority_id(client, admin)
        agent = await _create_agent(client, admin, dept_id, uid)

        source = await _make_ticket(client, admin, "Source ticket", type_id, prio_id)
        target = await _make_ticket(client, admin, "Target ticket", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{source['id']}/merge",
            json={"target_id": target["id"], "comment": "Дубль"},
            headers=agent["headers"],
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "merged"
        assert data["merged_into_id"] == target["id"]

    async def test_admin_can_merge(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"AType{uid}")
        prio_id = await _get_priority_id(client, admin)

        source = await _make_ticket(client, admin, "Source A", type_id, prio_id)
        target = await _make_ticket(client, admin, "Target A", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{source['id']}/merge",
            json={"target_id": target["id"]},
            headers=admin,
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "merged"

    async def test_user_cannot_merge(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        dept_id = await _create_dept(client, admin, f"UDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"UType{uid}", dept_id)
        prio_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)

        source = await _make_ticket(client, admin, "Source U", type_id, prio_id)
        target = await _make_ticket(client, admin, "Target U", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{source['id']}/merge",
            json={"target_id": target["id"]},
            headers=user["headers"],
        )
        assert r.status_code == 403

    async def test_cannot_merge_into_self(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"SelfType{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _make_ticket(client, admin, "Self merge", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/merge",
            json={"target_id": ticket["id"]},
            headers=admin,
        )
        assert r.status_code == 400

    async def test_cannot_merge_already_merged_source(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"AlrType{uid}")
        prio_id = await _get_priority_id(client, admin)

        s1 = await _make_ticket(client, admin, "S1", type_id, prio_id)
        s2 = await _make_ticket(client, admin, "S2", type_id, prio_id)
        t = await _make_ticket(client, admin, "Target T", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{s1['id']}/merge",
            json={"target_id": t["id"]},
            headers=admin,
        )
        assert r.status_code == 200

        r2 = await client.post(
            f"/api/v1/tickets/{s1['id']}/merge",
            json={"target_id": s2["id"]},
            headers=admin,
        )
        assert r2.status_code == 422

    async def test_cannot_merge_into_merged_target(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"TgtType{uid}")
        prio_id = await _get_priority_id(client, admin)

        s = await _make_ticket(client, admin, "Src X", type_id, prio_id)
        t1 = await _make_ticket(client, admin, "Tgt X1", type_id, prio_id)
        t2 = await _make_ticket(client, admin, "Tgt X2", type_id, prio_id)

        await client.post(
            f"/api/v1/tickets/{t1['id']}/merge",
            json={"target_id": t2["id"]},
            headers=admin,
        )
        r = await client.post(
            f"/api/v1/tickets/{s['id']}/merge",
            json={"target_id": t1["id"]},
            headers=admin,
        )
        assert r.status_code == 422

    async def test_source_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.post(
            "/api/v1/tickets/999999/merge",
            json={"target_id": 1},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_target_not_found(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"NfType{uid}")
        prio_id = await _get_priority_id(client, admin)
        source = await _make_ticket(client, admin, "Src NF", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{source['id']}/merge",
            json={"target_id": 999999},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_merge_requires_auth(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"AuthType{uid}")
        prio_id = await _get_priority_id(client, admin)
        source = await _make_ticket(client, admin, "Src Auth", type_id, prio_id)
        target = await _make_ticket(client, admin, "Tgt Auth", type_id, prio_id)

        r = await client.post(
            f"/api/v1/tickets/{source['id']}/merge",
            json={"target_id": target["id"]},
        )
        assert r.status_code in (401, 403)

    async def test_history_recorded_on_merge(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"HistType{uid}")
        prio_id = await _get_priority_id(client, admin)
        source = await _make_ticket(client, admin, "Src Hist", type_id, prio_id)
        target = await _make_ticket(client, admin, "Tgt Hist", type_id, prio_id)

        await client.post(
            f"/api/v1/tickets/{source['id']}/merge",
            json={"target_id": target["id"], "comment": "Комментарий"},
            headers=admin,
        )
        r = await client.get(f"/api/v1/tickets/{source['id']}/history", headers=admin)
        assert r.status_code == 200
        events = [e["event_type"] for e in r.json()]
        assert "merged" in events


# ---------------------------------------------------------------------------
# GET /{id}/merged
# ---------------------------------------------------------------------------

class TestGetMergedTickets:
    async def test_empty_list(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"EmptyType{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _make_ticket(client, admin, "Lonely ticket", type_id, prio_id)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/merged", headers=admin)
        assert r.status_code == 200
        assert r.json() == []

    async def test_returns_merged_tickets(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"ListType{uid}")
        prio_id = await _get_priority_id(client, admin)

        s1 = await _make_ticket(client, admin, "Merged S1", type_id, prio_id)
        s2 = await _make_ticket(client, admin, "Merged S2", type_id, prio_id)
        target = await _make_ticket(client, admin, "Target List", type_id, prio_id)

        for src in (s1, s2):
            await client.post(
                f"/api/v1/tickets/{src['id']}/merge",
                json={"target_id": target["id"]},
                headers=admin,
            )

        r = await client.get(f"/api/v1/tickets/{target['id']}/merged", headers=admin)
        assert r.status_code == 200
        ids = {t["id"] for t in r.json()}
        assert s1["id"] in ids
        assert s2["id"] in ids

    async def test_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/tickets/999999/merged", headers=admin)
        assert r.status_code == 404

    async def test_requires_auth(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"AuthMType{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _make_ticket(client, admin, "Auth merged list", type_id, prio_id)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/merged")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /{id}/duplicates
# ---------------------------------------------------------------------------

class TestFindDuplicates:
    async def test_returns_open_tickets(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"DupType{uid}")
        prio_id = await _get_priority_id(client, admin)

        base = await _make_ticket(client, admin, "Base dup check", type_id, prio_id)
        other = await _make_ticket(client, admin, "Other open ticket", type_id, prio_id)

        r = await client.get(f"/api/v1/tickets/{base['id']}/duplicates", headers=admin)
        assert r.status_code == 200
        ids = {t["id"] for t in r.json()}
        assert other["id"] in ids
        assert base["id"] not in ids

    async def test_search_by_title(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"SearchType{uid}")
        prio_id = await _get_priority_id(client, admin)

        base = await _make_ticket(client, admin, "Search base", type_id, prio_id)
        unique_name = f"xUnique{uid}x"
        await _make_ticket(client, admin, f"{unique_name} duplicate", type_id, prio_id)
        await _make_ticket(client, admin, "Unrelated ticket zzz", type_id, prio_id)

        r = await client.get(
            f"/api/v1/tickets/{base['id']}/duplicates",
            params={"q": unique_name},
            headers=admin,
        )
        assert r.status_code == 200
        titles = [t["title"] for t in r.json()]
        assert any(unique_name in t for t in titles)
        assert not any("Unrelated ticket zzz" in t for t in titles)

    async def test_excludes_merged(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"ExclType{uid}")
        prio_id = await _get_priority_id(client, admin)

        base = await _make_ticket(client, admin, "Dup base excl", type_id, prio_id)
        src = await _make_ticket(client, admin, "Will be merged dup", type_id, prio_id)
        tgt = await _make_ticket(client, admin, "Merge target dup", type_id, prio_id)

        await client.post(
            f"/api/v1/tickets/{src['id']}/merge",
            json={"target_id": tgt["id"]},
            headers=admin,
        )

        r = await client.get(f"/api/v1/tickets/{base['id']}/duplicates", headers=admin)
        ids = {t["id"] for t in r.json()}
        assert src["id"] not in ids

    async def test_user_forbidden(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"ForbType{uid}")
        prio_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)
        ticket = await _make_ticket(client, admin, "Forbidden dup", type_id, prio_id)

        r = await client.get(
            f"/api/v1/tickets/{ticket['id']}/duplicates",
            headers=user["headers"],
        )
        assert r.status_code == 403

    async def test_requires_auth(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"AuthDType{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _make_ticket(client, admin, "Auth dup", type_id, prio_id)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/duplicates")
        assert r.status_code in (401, 403)

    async def test_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/tickets/999999/duplicates", headers=admin)
        assert r.status_code == 404
