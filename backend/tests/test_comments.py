"""Integration tests for Comments API (Mission 07)."""
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
    username = f"cuser{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"CUser {suffix}", "role": "user"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_agent(client: AsyncClient, admin_headers: dict, dept_id: int, suffix: str = "") -> dict:
    username = f"cagent{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"CAgent {suffix}", "role": "agent", "department_id": dept_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_ticket(client: AsyncClient, headers: dict, priority_id: int, type_id: int, title: str = "Test") -> dict:
    r = await client.post(
        "/api/v1/tickets",
        json={"title": title, "description": "desc", "priority_id": priority_id, "type_id": type_id},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


async def _create_comment(client: AsyncClient, headers: dict, ticket_id: int, body: str = "Hello", is_internal: bool = False) -> dict:
    r = await client.post(
        f"/api/v1/tickets/{ticket_id}/comments",
        json={"body": body, "is_internal": is_internal},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# List comments
# ---------------------------------------------------------------------------

class TestListComments:
    async def test_list_comments_empty(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"LType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/comments", headers=admin)
        assert r.status_code == 200
        assert r.json() == []

    async def test_list_returns_public_comments(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"LPub{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        await _create_comment(client, admin, ticket["id"], "Public comment")

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/comments", headers=admin)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["body"] == "Public comment"

    async def test_user_cannot_see_internal_comments(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"InDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"InType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)
        agent = await _create_agent(client, admin, dept_id, uid)
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        await _create_comment(client, agent["headers"], ticket["id"], "Internal note", is_internal=True)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/comments", headers=user["headers"])
        assert r.status_code == 200
        internal = [c for c in r.json() if c["is_internal"]]
        assert len(internal) == 0

    async def test_agent_can_see_internal_comments(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"VisDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"VisType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        agent = await _create_agent(client, admin, dept_id, uid)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        await _create_comment(client, agent["headers"], ticket["id"], "Internal", is_internal=True)

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/comments", headers=agent["headers"])
        assert r.status_code == 200
        assert any(c["is_internal"] for c in r.json())

    async def test_list_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/tickets/1/comments")
        assert r.status_code == 403

    async def test_list_ticket_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/tickets/99999/comments", headers=admin)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Create comment
# ---------------------------------------------------------------------------

class TestCreateComment:
    async def test_create_public_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"CType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/comments",
            json={"body": "Hello there", "is_internal": False},
            headers=admin,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["body"] == "Hello there"
        assert data["is_internal"] is False
        assert data["ticket_id"] == ticket["id"]

    async def test_user_cannot_create_internal_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"UserIntType{uid}")
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/comments",
            json={"body": "Sneaky internal", "is_internal": True},
            headers=user["headers"],
        )
        assert r.status_code == 403

    async def test_agent_can_create_internal_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"AgIntDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"AgIntType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        agent = await _create_agent(client, admin, dept_id, uid)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/comments",
            json={"body": "Agent internal", "is_internal": True},
            headers=agent["headers"],
        )
        assert r.status_code == 201
        assert r.json()["is_internal"] is True

    async def test_create_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/tickets/1/comments", json={"body": "x"})
        assert r.status_code == 403

    async def test_create_on_nonexistent_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.post(
            "/api/v1/tickets/99999/comments",
            json={"body": "Ghost"},
            headers=admin,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Update comment
# ---------------------------------------------------------------------------

class TestUpdateComment:
    async def test_author_can_update_within_window(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"UpdType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        comment = await _create_comment(client, admin, ticket["id"], "Original body")

        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}/comments/{comment['id']}",
            json={"body": "Edited body"},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json()["body"] == "Edited body"

    async def test_non_author_cannot_update(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"NADept{uid}")
        type_id = await _create_ticket_type(client, admin, f"NAType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        agent = await _create_agent(client, admin, dept_id, uid)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        # Comment created by agent
        comment = await _create_comment(client, agent["headers"], ticket["id"], "Agent comment")

        # Admin (not the author) tries to update
        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}/comments/{comment['id']}",
            json={"body": "Hijacked"},
            headers=admin,
        )
        assert r.status_code == 403

    async def test_update_nonexistent_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"NoComType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}/comments/99999",
            json={"body": "Ghost"},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_update_requires_auth(self, client: AsyncClient):
        r = await client.put("/api/v1/tickets/1/comments/1", json={"body": "x"})
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Delete comment
# ---------------------------------------------------------------------------

class TestDeleteComment:
    async def test_author_can_delete_within_window(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"DelType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        comment = await _create_comment(client, admin, ticket["id"], "To delete")

        r = await client.delete(
            f"/api/v1/tickets/{ticket['id']}/comments/{comment['id']}",
            headers=admin,
        )
        assert r.status_code == 204

    async def test_admin_can_delete_any_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"AdDelDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"AdDelType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        agent = await _create_agent(client, admin, dept_id, uid)
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        comment = await _create_comment(client, agent["headers"], ticket["id"], "Agent comment")

        r = await client.delete(
            f"/api/v1/tickets/{ticket['id']}/comments/{comment['id']}",
            headers=admin,
        )
        assert r.status_code == 204

    async def test_delete_verifies_comment_belongs_to_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"WrongTkt{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket1 = await _create_ticket(client, admin, priority_id, type_id, "T1")
        ticket2 = await _create_ticket(client, admin, priority_id, type_id, "T2")
        comment = await _create_comment(client, admin, ticket1["id"], "Belongs to T1")

        # Try to delete using ticket2's id
        r = await client.delete(
            f"/api/v1/tickets/{ticket2['id']}/comments/{comment['id']}",
            headers=admin,
        )
        assert r.status_code == 404

    async def test_delete_nonexistent_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"NoCDelType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.delete(
            f"/api/v1/tickets/{ticket['id']}/comments/99999",
            headers=admin,
        )
        assert r.status_code == 404

    async def test_delete_requires_auth(self, client: AsyncClient):
        r = await client.delete("/api/v1/tickets/1/comments/1")
        assert r.status_code == 403
