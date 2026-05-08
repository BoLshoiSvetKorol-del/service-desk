"""Integration tests for Attachments API (Mission 07)."""
import io
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
    username = f"attuser{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"AttUser {suffix}", "role": "user"},
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


async def _create_ticket(client: AsyncClient, headers: dict, priority_id: int, type_id: int) -> dict:
    r = await client.post(
        "/api/v1/tickets",
        json={"title": "Att ticket", "priority_id": priority_id, "type_id": type_id},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def _fake_file(
    name: str = "test.txt",
    content: bytes = b"hello world",
    content_type: str = "text/plain",
) -> tuple:
    return ("file", (name, io.BytesIO(content), content_type))


# ---------------------------------------------------------------------------
# Upload to ticket
# ---------------------------------------------------------------------------

class TestUploadToTicket:
    async def test_upload_text_file(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"UpType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=admin,
            files=[_fake_file()],
        )
        assert r.status_code == 201
        data = r.json()
        assert data["ticket_id"] == ticket["id"]
        assert data["original_filename"] == "test.txt"
        assert data["mimetype"] == "text/plain"
        assert data["size_bytes"] > 0
        assert data["url"].startswith("/uploads/")

    async def test_upload_pdf(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"PdfType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=admin,
            files=[_fake_file("doc.pdf", b"%PDF-1.4 fake content", "application/pdf")],
        )
        assert r.status_code == 201
        assert r.json()["mimetype"] == "application/pdf"

    async def test_upload_disallowed_mime_rejected(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"BadMime{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=admin,
            files=[_fake_file("evil.exe", b"MZ\x90\x00", "application/x-msdownload")],
        )
        assert r.status_code == 400

    async def test_upload_requires_auth(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/tickets/1/attachments",
            files=[_fake_file()],
        )
        assert r.status_code == 403

    async def test_upload_to_nonexistent_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.post(
            "/api/v1/tickets/99999/attachments",
            headers=admin,
            files=[_fake_file()],
        )
        assert r.status_code == 404

    async def test_user_can_upload_to_own_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"UserUpType{uid}")
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=user["headers"],
            files=[_fake_file("user_doc.txt")],
        )
        assert r.status_code == 201

    async def test_user_cannot_upload_to_others_ticket(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"OtherUpType{uid}")
        priority_id = await _get_priority_id(client, admin)
        # Admin creates ticket
        ticket = await _create_ticket(client, admin, priority_id, type_id)
        # User tries to upload
        user = await _create_user(client, admin, uid)
        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=user["headers"],
            files=[_fake_file()],
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Upload to comment
# ---------------------------------------------------------------------------

class TestUploadToComment:
    async def test_upload_to_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"ComUpType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        # Create a comment first
        cr = await client.post(
            f"/api/v1/tickets/{ticket['id']}/comments",
            json={"body": "Comment with attachment"},
            headers=admin,
        )
        assert cr.status_code == 201
        comment_id = cr.json()["id"]

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/comments/{comment_id}/attachments",
            headers=admin,
            files=[_fake_file("comment_att.txt")],
        )
        assert r.status_code == 201
        data = r.json()
        assert data["comment_id"] == comment_id
        assert data["ticket_id"] == ticket["id"]

    async def test_upload_to_nonexistent_comment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"NoCComType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/comments/99999/attachments",
            headers=admin,
            files=[_fake_file()],
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Download & Delete
# ---------------------------------------------------------------------------

class TestDownloadDeleteAttachment:
    async def test_download_nonexistent(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/attachments/99999", headers=admin)
        assert r.status_code == 404

    async def test_download_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/attachments/1")
        assert r.status_code == 403

    async def test_delete_own_attachment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"DelAttType{uid}")
        priority_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, priority_id, type_id)

        up = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=admin,
            files=[_fake_file("todelete.txt")],
        )
        assert up.status_code == 201
        att_id = up.json()["id"]

        r = await client.delete(f"/api/v1/attachments/{att_id}", headers=admin)
        assert r.status_code == 204

    async def test_delete_nonexistent_attachment(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.delete("/api/v1/attachments/99999", headers=admin)
        assert r.status_code == 404

    async def test_delete_requires_auth(self, client: AsyncClient):
        r = await client.delete("/api/v1/attachments/1")
        assert r.status_code == 403

    async def test_user_cannot_delete_others_attachment(self, client: AsyncClient):
        admin = await _auth(client)
        uid = uuid.uuid4().hex[:6]
        type_id = await _create_ticket_type(client, admin, f"OthDelType{uid}")
        priority_id = await _get_priority_id(client, admin)
        user = await _create_user(client, admin, uid)
        ticket = await _create_ticket(client, user["headers"], priority_id, type_id)

        # User uploads
        up = await client.post(
            f"/api/v1/tickets/{ticket['id']}/attachments",
            headers=user["headers"],
            files=[_fake_file("mine.txt")],
        )
        assert up.status_code == 201
        att_id = up.json()["id"]

        # Another user created separately
        uid2 = uuid.uuid4().hex[:6]
        user2 = await _create_user(client, admin, uid2)

        # user2 cannot access the ticket (it belongs to user) → 403
        r = await client.delete(f"/api/v1/attachments/{att_id}", headers=user2["headers"])
        assert r.status_code == 403
