"""Integration tests for Notifications API (Mission 10)."""
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


async def _create_user(client: AsyncClient, admin_headers: dict, suffix: str = "") -> dict:
    username = f"nuser{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"NUser {suffix}", "role": "user"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_agent(client: AsyncClient, admin_headers: dict, dept_id: int, suffix: str = "") -> dict:
    username = f"nagent{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"NAgent {suffix}", "role": "agent", "department_id": dept_id},
        headers=admin_headers,
    )
    assert r.status_code == 201
    token = await _login(client, username, "pass123")
    return {"id": r.json()["id"], "headers": {"Authorization": f"Bearer {token}"}}


async def _create_dept(client: AsyncClient, headers: dict, name: str) -> int:
    r = await client.post("/api/v1/departments", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _get_priority_id(client: AsyncClient, headers: dict, level: str = "normal") -> int:
    r = await client.get("/api/v1/priorities", headers=headers)
    return next(p["id"] for p in r.json() if p["level"] == level)


async def _create_ticket_type(client: AsyncClient, headers: dict, name: str, dept_id: int | None = None) -> int:
    payload: dict = {"name": name}
    if dept_id:
        payload["default_department_id"] = dept_id
    r = await client.post("/api/v1/ticket-types", json=payload, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def _insert_notification(db_session: AsyncSession, user_id: int, ticket_id: int | None = None) -> int:
    """Insert a test notification directly into DB."""
    from app.models.notification import Notification
    notif = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        event_type="ticket_created",
        message="Test notification",
        is_read=False,
    )
    db_session.add(notif)
    await db_session.commit()
    await db_session.refresh(notif)
    return notif.id


async def _get_current_user_id(client: AsyncClient, headers: dict) -> int:
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    return r.json()["id"]


# ---------------------------------------------------------------------------
# List notifications
# ---------------------------------------------------------------------------

class TestListNotifications:
    async def test_list_returns_paginated_structure(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/notifications", headers=admin)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_notifications_require_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/notifications")
        assert r.status_code == 403

    async def test_notifications_are_user_scoped(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)

        admin_id = await _get_current_user_id(client, admin)
        await _insert_notification(db_session, admin_id)

        r = await client.get("/api/v1/notifications", headers=user["headers"])
        assert r.status_code == 200
        # User has no notifications of their own
        user_id = await _get_current_user_id(client, user["headers"])
        for item in r.json()["items"]:
            assert item["user_id"] == user_id

    async def test_own_notification_appears_in_list(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)

        user_id = await _get_current_user_id(client, user["headers"])
        await _insert_notification(db_session, user_id)

        r = await client.get("/api/v1/notifications", headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_filter_by_is_read_false(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)
        user_id = await _get_current_user_id(client, user["headers"])
        await _insert_notification(db_session, user_id)

        r = await client.get("/api/v1/notifications?is_read=false", headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        for item in r.json()["items"]:
            assert item["is_read"] is False

    async def test_filter_by_is_read_true_shows_nothing_for_fresh_user(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)
        user_id = await _get_current_user_id(client, user["headers"])
        await _insert_notification(db_session, user_id)  # unread

        r = await client.get("/api/v1/notifications?is_read=true", headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_pagination_params(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/notifications?page=1&page_size=5", headers=admin)
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1

    async def test_notification_created_on_status_change(self, client: AsyncClient, db_session: AsyncSession):
        """When agent changes ticket status, the requester gets a notification via notify_ticket_event."""
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        dept_id = await _create_dept(client, admin, f"NotiDept{uid}")
        type_id = await _create_ticket_type(client, admin, f"NotiType{uid}", dept_id)
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)
        agent = await _create_agent(client, admin, dept_id, uid)

        ticket_r = await client.post(
            "/api/v1/tickets",
            json={"title": "Notify ticket", "priority_id": priority_id, "type_id": type_id},
            headers=user["headers"],
        )
        assert ticket_r.status_code == 201
        ticket_id = ticket_r.json()["id"]

        # Agent changes status → user gets notification
        await client.patch(
            f"/api/v1/tickets/{ticket_id}/status",
            json={"status": "in_progress"},
            headers=agent["headers"],
        )

        user_id = await _get_current_user_id(client, user["headers"])
        r = await client.get("/api/v1/notifications", headers=user["headers"])
        notif_items = [n for n in r.json()["items"] if n.get("ticket_id") == ticket_id]
        assert len(notif_items) >= 1


# ---------------------------------------------------------------------------
# Mark notification as read
# ---------------------------------------------------------------------------

class TestMarkRead:
    async def test_mark_single_as_read(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)
        user_id = await _get_current_user_id(client, user["headers"])
        notif_id = await _insert_notification(db_session, user_id)

        r = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["is_read"] is True

    async def test_mark_read_idempotent(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)
        user_id = await _get_current_user_id(client, user["headers"])
        notif_id = await _insert_notification(db_session, user_id)

        await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=user["headers"])
        r = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["is_read"] is True

    async def test_cannot_mark_others_notification(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)

        admin_id = await _get_current_user_id(client, admin)
        notif_id = await _insert_notification(db_session, admin_id)

        r = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=user["headers"])
        assert r.status_code == 403

    async def test_mark_nonexistent_returns_404(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.patch("/api/v1/notifications/99999/read", headers=admin)
        assert r.status_code == 404

    async def test_mark_read_requires_auth(self, client: AsyncClient):
        r = await client.patch("/api/v1/notifications/1/read")
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Mark all as read
# ---------------------------------------------------------------------------

class TestMarkAllRead:
    async def test_mark_all_read(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user = await _create_user(client, admin, uid)
        user_id = await _get_current_user_id(client, user["headers"])

        await _insert_notification(db_session, user_id)
        await _insert_notification(db_session, user_id)

        r = await client.patch("/api/v1/notifications/read-all", headers=user["headers"])
        assert r.status_code == 204

        # All unread should be gone
        r = await client.get("/api/v1/notifications?is_read=false", headers=user["headers"])
        assert r.json()["total"] == 0

    async def test_mark_all_read_does_not_affect_other_users(self, client: AsyncClient, db_session: AsyncSession):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        user_a = await _create_user(client, admin, uid + "a")
        user_b = await _create_user(client, admin, uid + "b")

        user_b_id = await _get_current_user_id(client, user_b["headers"])
        await _insert_notification(db_session, user_b_id)

        # User A marks all their read (they have none)
        await client.patch("/api/v1/notifications/read-all", headers=user_a["headers"])

        # User B's notification should still be unread
        r = await client.get("/api/v1/notifications?is_read=false", headers=user_b["headers"])
        assert r.json()["total"] >= 1

    async def test_mark_all_read_requires_auth(self, client: AsyncClient):
        r = await client.patch("/api/v1/notifications/read-all")
        assert r.status_code == 403
