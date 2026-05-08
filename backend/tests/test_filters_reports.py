"""Integration tests for Saved Filters and Reports (Mission 09)."""
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


async def _create_user(client: AsyncClient, admin_headers: dict, suffix: str = "", role: str = "user") -> dict:
    username = f"fruser{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"FR User {suffix}", "role": role},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_ticket_type(client: AsyncClient, headers: dict, name: str) -> int:
    r = await client.post("/api/v1/ticket-types", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _get_priority_id(client: AsyncClient, headers: dict, level: str = "normal") -> int:
    r = await client.get("/api/v1/priorities", headers=headers)
    return next(p["id"] for p in r.json() if p["level"] == level)


# ---------------------------------------------------------------------------
# Saved Filters
# ---------------------------------------------------------------------------

class TestSavedFilters:
    async def test_list_filters_empty_initially(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)
        r = await client.get("/api/v1/filters", headers=user["headers"])
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_create_filter(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.post(
            "/api/v1/filters",
            json={"name": "Open critical", "filter_params": {"status": "new", "priority": "critical"}},
            headers=admin,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Open critical"
        assert data["filter_params"]["status"] == "new"
        assert "id" in data

    async def test_created_filter_appears_in_list(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)

        await client.post(
            "/api/v1/filters",
            json={"name": f"UserFilter{uid}", "filter_params": {}},
            headers=user["headers"],
        )
        r = await client.get("/api/v1/filters", headers=user["headers"])
        assert r.status_code == 200
        names = [f["name"] for f in r.json()]
        assert f"UserFilter{uid}" in names

    async def test_filter_is_user_scoped(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)

        await client.post(
            "/api/v1/filters",
            json={"name": f"AdminPrivate{uid}", "filter_params": {}},
            headers=admin,
        )

        # User should not see admin's filter
        r = await client.get("/api/v1/filters", headers=user["headers"])
        assert r.status_code == 200
        names = [f["name"] for f in r.json()]
        assert f"AdminPrivate{uid}" not in names

    async def test_delete_own_filter(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.post(
            "/api/v1/filters",
            json={"name": "Delete me", "filter_params": {}},
            headers=admin,
        )
        filter_id = r.json()["id"]

        r = await client.delete(f"/api/v1/filters/{filter_id}", headers=admin)
        assert r.status_code == 204

    async def test_cannot_delete_others_filter(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)

        # Admin creates filter
        r = await client.post(
            "/api/v1/filters",
            json={"name": "Admin only", "filter_params": {}},
            headers=admin,
        )
        filter_id = r.json()["id"]

        r = await client.delete(f"/api/v1/filters/{filter_id}", headers=user["headers"])
        assert r.status_code == 403

    async def test_delete_nonexistent_filter(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.delete("/api/v1/filters/99999", headers=admin)
        assert r.status_code == 404

    async def test_filters_require_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/filters")
        assert r.status_code == 403

    async def test_create_filter_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/filters", json={"name": "x", "filter_params": {}})
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class TestReports:
    async def test_tickets_count_returns_structure(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/tickets-count", headers=admin)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_tickets_count_groupby_week(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/tickets-count?groupby=week", headers=admin)
        assert r.status_code == 200

    async def test_tickets_count_groupby_month(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/tickets-count?groupby=month", headers=admin)
        assert r.status_code == 200

    async def test_tickets_count_with_date_range(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get(
            "/api/v1/reports/tickets-count?date_from=2026-01-01&date_to=2026-12-31",
            headers=admin,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["total"], int)

    async def test_by_status_returns_list(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/by-status", headers=admin)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        for item in r.json():
            assert "status" in item
            assert "count" in item

    async def test_avg_resolution_time_returns_list(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/avg-resolution-time", headers=admin)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_sla_compliance_structure(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/sla-compliance", headers=admin)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "compliant" in data
        assert "compliance_rate" in data
        assert data["compliant"] <= data["total"]

    async def test_export_csv_content_type(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/export?format=csv", headers=admin)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "tickets.csv" in r.headers.get("content-disposition", "")

    async def test_export_xlsx_content_type(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/reports/export?format=xlsx", headers=admin)
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers.get("content-type", "")
        assert "tickets.xlsx" in r.headers.get("content-disposition", "")

    async def test_reports_forbidden_for_regular_user(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid, role="user")

        for endpoint in [
            "/api/v1/reports/tickets-count",
            "/api/v1/reports/by-status",
            "/api/v1/reports/avg-resolution-time",
            "/api/v1/reports/sla-compliance",
            "/api/v1/reports/export",
        ]:
            r = await client.get(endpoint, headers=user["headers"])
            assert r.status_code == 403, f"Expected 403 for {endpoint}, got {r.status_code}"

    async def test_reports_accessible_by_agent(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        agent = await _create_user(client, admin, uid, role="agent")

        r = await client.get("/api/v1/reports/tickets-count", headers=agent["headers"])
        assert r.status_code == 200

    async def test_reports_require_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/reports/tickets-count")
        assert r.status_code == 403

    async def test_sla_compliance_rate_in_range(self, client: AsyncClient):
        admin = await _auth(client)
        # First create a ticket so there's data
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"SLARepType{uid}")
        priority_id = await _get_priority_id(client, admin)
        await client.post(
            "/api/v1/tickets",
            json={"title": "SLA report ticket", "priority_id": priority_id, "type_id": type_id},
            headers=admin,
        )

        r = await client.get("/api/v1/reports/sla-compliance", headers=admin)
        data = r.json()
        assert 0.0 <= data["compliance_rate"] <= 100.0
