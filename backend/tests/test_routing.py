"""Tests for auto-routing rules: service logic and API endpoints."""
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
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def _admin_headers(client: AsyncClient) -> dict:
    token = await _login(client)
    return {"Authorization": f"Bearer {token}"}


async def _create_dept(client: AsyncClient, headers: dict, name: str) -> int:
    r = await client.post("/api/v1/departments", json={"name": name}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _create_type(client: AsyncClient, headers: dict, name: str) -> int:
    r = await client.post("/api/v1/ticket-types", json={"name": name}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _create_rule(client: AsyncClient, headers: dict, **kwargs) -> dict:
    r = await client.post("/api/v1/routing-rules", json=kwargs, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------

class TestRoutingService:
    async def test_no_rules_returns_none(self, db_session: AsyncSession):
        from app.services.routing_service import find_matching_rule
        result = await find_matching_rule(db_session, "Some title", "Some description", type_id=None)
        assert result is None

    async def test_keyword_match_in_title(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        dept = Department(name="IT-svc-unit")
        db_session.add(dept)
        await db_session.flush()
        rule = RoutingRule(name="Printer rule", keywords="принтер, сканер", department_id=dept.id)
        db_session.add(rule)
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        result = await find_matching_rule(db_session, "не работает принтер", None, type_id=None)
        assert result is not None
        assert result.id == rule.id

    async def test_keyword_match_in_description(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        dept = Department(name="IT-svc-desc")
        db_session.add(dept)
        await db_session.flush()
        rule = RoutingRule(name="Network rule", keywords="сеть, vpn", department_id=dept.id)
        db_session.add(rule)
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        result = await find_matching_rule(db_session, "Проблема с подключением", "vpn не работает", type_id=None)
        assert result is not None
        assert result.id == rule.id

    async def test_keyword_case_insensitive(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        dept = Department(name="IT-svc-case")
        db_session.add(dept)
        await db_session.flush()
        rule = RoutingRule(name="Case test", keywords="Принтер", department_id=dept.id)
        db_session.add(rule)
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        result = await find_matching_rule(db_session, "ПРИНТЕР сломался", None, type_id=None)
        assert result is not None

    async def test_type_condition_match(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        from app.models.ticket_type import TicketType
        dept = Department(name="HR-svc")
        db_session.add(dept)
        await db_session.flush()
        tt = TicketType(name="HR-тип-svc", is_active=True)
        db_session.add(tt)
        await db_session.flush()
        rule = RoutingRule(name="HR tickets", ticket_type_id=tt.id, department_id=dept.id)
        db_session.add(rule)
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        # Matches when type is correct
        result = await find_matching_rule(db_session, "Любой текст", None, type_id=tt.id)
        assert result is not None and result.id == rule.id
        # Does not match when type is wrong
        result2 = await find_matching_rule(db_session, "Любой текст", None, type_id=tt.id + 999)
        assert result2 is None

    async def test_both_conditions_must_match(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        from app.models.ticket_type import TicketType
        dept = Department(name="Combo-dept")
        db_session.add(dept)
        await db_session.flush()
        tt = TicketType(name="Combo-type", is_active=True)
        db_session.add(tt)
        await db_session.flush()
        rule = RoutingRule(
            name="Combo rule",
            keywords="ключевое",
            ticket_type_id=tt.id,
            department_id=dept.id,
        )
        db_session.add(rule)
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        # Correct type but keyword missing → no match
        assert await find_matching_rule(db_session, "другой текст", None, type_id=tt.id) is None
        # Keyword present but wrong type → no match
        assert await find_matching_rule(db_session, "ключевое слово", None, type_id=tt.id + 999) is None
        # Both correct → match
        assert await find_matching_rule(db_session, "ключевое слово", None, type_id=tt.id) is not None

    async def test_inactive_rule_skipped(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        dept = Department(name="Inactive-dept")
        db_session.add(dept)
        await db_session.flush()
        rule = RoutingRule(name="Disabled", keywords="неактивно", department_id=dept.id, is_active=False)
        db_session.add(rule)
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        result = await find_matching_rule(db_session, "неактивно", None, type_id=None)
        assert result is None

    async def test_first_rule_wins_by_priority(self, db_session: AsyncSession):
        from app.models.routing_rule import RoutingRule
        from app.models.department import Department
        dept_a = Department(name="Prio-A")
        dept_b = Department(name="Prio-B")
        db_session.add_all([dept_a, dept_b])
        await db_session.flush()
        rule_low = RoutingRule(name="Low prio", keywords="общий", department_id=dept_a.id, priority=10)
        rule_high = RoutingRule(name="High prio", keywords="общий", department_id=dept_b.id, priority=1)
        db_session.add_all([rule_low, rule_high])
        await db_session.flush()

        from app.services.routing_service import find_matching_rule
        result = await find_matching_rule(db_session, "общий вопрос", None, type_id=None)
        assert result is not None
        assert result.id == rule_high.id  # priority=1 wins over priority=10


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------

class TestRoutingRulesAPI:
    async def test_crud_lifecycle(self, client: AsyncClient):
        headers = await _admin_headers(client)
        dept_id = await _create_dept(client, headers, "IT-API-test")

        # Create
        rule = await _create_rule(
            client, headers,
            name="Test API rule",
            keywords="сервер, хост",
            department_id=dept_id,
            priority=5,
            is_active=True,
        )
        rule_id = rule["id"]
        assert rule["name"] == "Test API rule"
        assert rule["keywords"] == "сервер, хост"
        assert rule["department"]["id"] == dept_id
        assert rule["priority"] == 5

        # List
        r = await client.get("/api/v1/routing-rules", headers=headers)
        assert r.status_code == 200
        ids = [rr["id"] for rr in r.json()]
        assert rule_id in ids

        # Update
        r = await client.put(f"/api/v1/routing-rules/{rule_id}",
                             json={"name": "Updated rule", "is_active": False},
                             headers=headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Updated rule"
        assert r.json()["is_active"] is False

        # Delete
        r = await client.delete(f"/api/v1/routing-rules/{rule_id}", headers=headers)
        assert r.status_code == 204

        r = await client.get("/api/v1/routing-rules", headers=headers)
        assert all(rr["id"] != rule_id for rr in r.json())

    async def test_invalid_department_rejected(self, client: AsyncClient):
        headers = await _admin_headers(client)
        r = await client.post("/api/v1/routing-rules",
                              json={"name": "Bad rule", "department_id": 999999},
                              headers=headers)
        assert r.status_code == 404

    async def test_non_admin_cannot_create(self, client: AsyncClient):
        headers = await _admin_headers(client)
        dept_id = await _create_dept(client, headers, "No-Access-Dept")
        # Register a plain user
        r = await client.post("/api/v1/auth/register",
                              json={"email": "routeuser@test.com", "password": "pass1234", "full_name": "Route User"})
        assert r.status_code in (200, 201)
        token = (await client.post("/api/v1/auth/login",
                                   json={"username": "routeuser@test.com", "password": "pass1234"})).json()["access_token"]
        user_headers = {"Authorization": f"Bearer {token}"}

        r = await client.post("/api/v1/routing-rules",
                              json={"name": "Hack", "department_id": dept_id},
                              headers=user_headers)
        assert r.status_code == 403

    async def test_test_endpoint_match(self, client: AsyncClient):
        headers = await _admin_headers(client)
        dept_id = await _create_dept(client, headers, "Test-Endpoint-Dept")
        await _create_rule(client, headers, name="Email rule",
                           keywords="почта, email, outlook",
                           department_id=dept_id, priority=0)

        r = await client.post("/api/v1/routing-rules/test",
                              json={"title": "не работает email"},
                              headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["matched"] is True
        assert data["department_name"] == "Test-Endpoint-Dept"

    async def test_test_endpoint_no_match(self, client: AsyncClient):
        headers = await _admin_headers(client)
        r = await client.post("/api/v1/routing-rules/test",
                              json={"title": "вопрос без ключевых слов xyz123"},
                              headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["matched"] is False
        assert data["fallback_used"] is True

    async def test_ticket_creation_applies_routing(self, client: AsyncClient):
        """End-to-end: creating a ticket should auto-assign department from rule."""
        headers = await _admin_headers(client)
        dept_id = await _create_dept(client, headers, "Auto-Route-Dept-E2E")
        type_id = await _create_type(client, headers, "Auto-Route-Type-E2E")
        await _create_rule(client, headers,
                           name="E2E routing rule",
                           keywords="автороутинг_тест",
                           department_id=dept_id,
                           priority=0)

        r = await client.post(
            "/api/v1/tickets",
            json={"title": "автороутинг_тест проблема", "type_id": type_id},
            headers=headers,
        )
        assert r.status_code == 201, r.text
        ticket = r.json()
        assert ticket["department_id"] == dept_id, (
            f"Expected department_id={dept_id}, got {ticket['department_id']}"
        )

    async def test_ticket_creation_falls_back_to_type_default(self, client: AsyncClient):
        """When no rule matches, ticket gets the type's default department."""
        headers = await _admin_headers(client)
        dept_id = await _create_dept(client, headers, "Type-Default-Dept-E2E")
        type_id = await _create_type(client, headers, "Type-Default-Type-E2E")
        # Set default_department on ticket type
        await client.put(f"/api/v1/ticket-types/{type_id}",
                         json={"default_department_id": dept_id},
                         headers=headers)

        r = await client.post(
            "/api/v1/tickets",
            json={"title": "обычная заявка без ключевых слов", "type_id": type_id},
            headers=headers,
        )
        assert r.status_code == 201, r.text
        assert r.json()["department_id"] == dept_id
