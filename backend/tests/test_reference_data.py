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


async def _login(client: AsyncClient, username="admin", password="changeme") -> str:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


async def _auth(client: AsyncClient) -> dict:
    token = await _login(client)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Priorities
# ---------------------------------------------------------------------------

class TestPriorities:
    async def test_list_priorities(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/priorities", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 4
        levels = {p["level"] for p in data}
        assert levels == {"low", "normal", "high", "critical"}

    async def test_priority_sla_hours(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/priorities", headers=headers)
        by_level = {p["level"]: p["sla_hours"] for p in r.json()}
        assert by_level["low"] == 24
        assert by_level["normal"] == 8
        assert by_level["high"] == 4
        assert by_level["critical"] == 1

    async def test_priorities_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/priorities")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Ticket Types
# ---------------------------------------------------------------------------

class TestTicketTypes:
    async def test_create_ticket_type(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.post(
            "/api/v1/ticket-types",
            json={"name": "Техническая поддержка", "service_type": "IT", "work_direction": "Hardware"},
            headers=headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Техническая поддержка"
        assert data["service_type"] == "IT"
        assert data["is_active"] is True

    async def test_create_ticket_type_duplicate(self, client: AsyncClient):
        headers = await _auth(client)
        await client.post("/api/v1/ticket-types", json={"name": "DupType"}, headers=headers)
        r = await client.post("/api/v1/ticket-types", json={"name": "DupType"}, headers=headers)
        assert r.status_code == 409

    async def test_list_ticket_types(self, client: AsyncClient):
        headers = await _auth(client)
        await client.post("/api/v1/ticket-types", json={"name": "ListType1"}, headers=headers)
        r = await client.get("/api/v1/ticket-types", headers=headers)
        assert r.status_code == 200
        names = [t["name"] for t in r.json()]
        assert "ListType1" in names

    async def test_get_ticket_type(self, client: AsyncClient):
        headers = await _auth(client)
        create_r = await client.post("/api/v1/ticket-types", json={"name": "GetMe"}, headers=headers)
        tt_id = create_r.json()["id"]
        r = await client.get(f"/api/v1/ticket-types/{tt_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["id"] == tt_id

    async def test_get_ticket_type_not_found(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/ticket-types/99999", headers=headers)
        assert r.status_code == 404

    async def test_update_ticket_type(self, client: AsyncClient):
        headers = await _auth(client)
        create_r = await client.post("/api/v1/ticket-types", json={"name": "ToUpdate"}, headers=headers)
        tt_id = create_r.json()["id"]
        r = await client.put(
            f"/api/v1/ticket-types/{tt_id}",
            json={"name": "Updated", "is_active": False},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"
        assert r.json()["is_active"] is False

    async def test_delete_ticket_type(self, client: AsyncClient):
        headers = await _auth(client)
        create_r = await client.post("/api/v1/ticket-types", json={"name": "ToDeleteTT"}, headers=headers)
        tt_id = create_r.json()["id"]
        r = await client.delete(f"/api/v1/ticket-types/{tt_id}", headers=headers)
        assert r.status_code == 204
        r2 = await client.get(f"/api/v1/ticket-types/{tt_id}", headers=headers)
        assert r2.status_code == 404

    async def test_ticket_type_with_department(self, client: AsyncClient):
        headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "TT Dept"}, headers=headers)
        dept_id = dept_r.json()["id"]
        r = await client.post(
            "/api/v1/ticket-types",
            json={"name": "Routing Type", "default_department_id": dept_id},
            headers=headers,
        )
        assert r.status_code == 201
        assert r.json()["default_department_id"] == dept_id

    async def test_ticket_type_invalid_department(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.post(
            "/api/v1/ticket-types",
            json={"name": "BadDeptType", "default_department_id": 99999},
            headers=headers,
        )
        assert r.status_code == 404

    async def test_ticket_types_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/ticket-types")
        assert r.status_code == 403

    async def test_create_ticket_type_requires_admin(self, client: AsyncClient):
        admin_headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "TTAgentDept"}, headers=admin_headers)
        dept_id = dept_r.json()["id"]
        await client.post(
            "/api/v1/users",
            json={
                "username": "tt_agent", "email": "tt_agent@test.com",
                "password": "pass123", "full_name": "TT Agent",
                "role": "agent", "department_id": dept_id,
            },
            headers=admin_headers,
        )
        token = (await client.post(
            "/api/v1/auth/login", json={"username": "tt_agent", "password": "pass123"}
        )).json()["access_token"]
        agent_headers = {"Authorization": f"Bearer {token}"}

        r = await client.post("/api/v1/ticket-types", json={"name": "Blocked"}, headers=agent_headers)
        assert r.status_code == 403
