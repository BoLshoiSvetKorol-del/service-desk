"""Integration tests for Tags & Notes (Mission 16)."""
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
    return {"Authorization": f"Bearer {await _login(client, username, password)}"}


async def _create_agent(client: AsyncClient, admin: dict, suffix: str) -> dict:
    dept_r = await client.post("/api/v1/departments", json={"name": f"Dept{suffix}"}, headers=admin)
    assert dept_r.status_code == 201
    dept_id = dept_r.json()["id"]
    username = f"tnagent{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"Agent {suffix}", "role": "agent", "department_id": dept_id},
        headers=admin,
    )
    assert r.status_code == 201
    return {"id": r.json()["id"], "dept_id": dept_id, "headers": await _auth(client, username, "pass123")}


async def _create_user(client: AsyncClient, admin: dict, suffix: str) -> dict:
    username = f"tnuser{suffix}"
    r = await client.post(
        "/api/v1/users",
        json={"username": username, "email": f"{username}@test.com", "password": "pass123",
              "full_name": f"User {suffix}", "role": "user"},
        headers=admin,
    )
    assert r.status_code == 201
    return {"id": r.json()["id"], "headers": await _auth(client, username, "pass123")}


async def _create_ticket_type(client: AsyncClient, admin: dict, name: str) -> int:
    r = await client.post("/api/v1/ticket-types", json={"name": name}, headers=admin)
    assert r.status_code == 201
    return r.json()["id"]


async def _get_priority_id(client: AsyncClient, admin: dict) -> int:
    r = await client.get("/api/v1/priorities", headers=admin)
    return next(p["id"] for p in r.json() if p["level"] == "normal")


async def _create_ticket(
    client: AsyncClient, headers: dict, type_id: int, priority_id: int, title: str,
    department_id: int | None = None
) -> dict:
    payload: dict = {"title": title, "priority_id": priority_id, "type_id": type_id}
    if department_id:
        payload["department_id"] = department_id
    r = await client.post("/api/v1/tickets", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


async def _create_tag(client: AsyncClient, admin: dict, name: str, color: str = "#1677ff") -> dict:
    r = await client.post("/api/v1/tags", json={"name": name, "color_hex": color}, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Tags CRUD
# ---------------------------------------------------------------------------

class TestTagsCRUD:
    async def test_list_tags_empty(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.get("/api/v1/tags", headers=admin)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_create_tag(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        r = await client.post("/api/v1/tags", json={"name": f"tag{uid}", "color_hex": "#ff0000"}, headers=admin)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == f"tag{uid}"
        assert data["color_hex"] == "#ff0000"

    async def test_create_tag_default_color(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        r = await client.post("/api/v1/tags", json={"name": f"deftag{uid}"}, headers=admin)
        assert r.status_code == 201
        assert r.json()["color_hex"] == "#1677ff"

    async def test_duplicate_tag_409(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        name = f"dup{uid}"
        await client.post("/api/v1/tags", json={"name": name}, headers=admin)
        r = await client.post("/api/v1/tags", json={"name": name}, headers=admin)
        assert r.status_code == 409

    async def test_user_cannot_create_tag(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        user = await _create_user(client, admin, uid)
        r = await client.post("/api/v1/tags", json={"name": f"usertag{uid}"}, headers=user["headers"])
        assert r.status_code == 403

    async def test_agent_can_create_tag(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        agent = await _create_agent(client, admin, uid)
        r = await client.post("/api/v1/tags", json={"name": f"agenttag{uid}"}, headers=agent["headers"])
        assert r.status_code == 201

    async def test_tag_appears_in_list(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        tag = await _create_tag(client, admin, f"listed{uid}")
        r = await client.get("/api/v1/tags", headers=admin)
        names = [t["name"] for t in r.json()]
        assert tag["name"] in names

    async def test_delete_tag_admin(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        tag = await _create_tag(client, admin, f"deltag{uid}")
        r = await client.delete(f"/api/v1/tags/{tag['id']}", headers=admin)
        assert r.status_code == 204

    async def test_delete_tag_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.delete("/api/v1/tags/999999", headers=admin)
        assert r.status_code == 404

    async def test_agent_cannot_delete_tag(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        agent = await _create_agent(client, admin, uid)
        tag = await _create_tag(client, admin, f"nodelagent{uid}")
        r = await client.delete(f"/api/v1/tags/{tag['id']}", headers=agent["headers"])
        assert r.status_code == 403

    async def test_tag_invalid_color(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        r = await client.post("/api/v1/tags", json={"name": f"badcolor{uid}", "color_hex": "red"}, headers=admin)
        assert r.status_code == 422

    async def test_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/tags")
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Ticket Tags (assign tags to ticket)
# ---------------------------------------------------------------------------

class TestTicketTags:
    async def test_set_tags_on_ticket(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"TT{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Tagged ticket")
        tag1 = await _create_tag(client, admin, f"t1{uid}")
        tag2 = await _create_tag(client, admin, f"t2{uid}")

        r = await client.put(
            f"/api/v1/tags/tickets/{ticket['id']}/tags",
            json={"tag_ids": [tag1["id"], tag2["id"]]},
            headers=admin,
        )
        assert r.status_code == 200
        names = {t["name"] for t in r.json()}
        assert tag1["name"] in names
        assert tag2["name"] in names

    async def test_ticket_response_includes_tags(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"TR{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Ticket with tags")
        tag = await _create_tag(client, admin, f"resp{uid}")

        await client.put(
            f"/api/v1/tags/tickets/{ticket['id']}/tags",
            json={"tag_ids": [tag["id"]]},
            headers=admin,
        )

        r = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=admin)
        assert r.status_code == 200
        tag_names = [t["name"] for t in r.json()["tags"]]
        assert tag["name"] in tag_names

    async def test_clear_tags(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"CLR{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Clear tags ticket")
        tag = await _create_tag(client, admin, f"clr{uid}")

        await client.put(
            f"/api/v1/tags/tickets/{ticket['id']}/tags",
            json={"tag_ids": [tag["id"]]},
            headers=admin,
        )
        r = await client.put(
            f"/api/v1/tags/tickets/{ticket['id']}/tags",
            json={"tag_ids": []},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json() == []

    async def test_ticket_not_found(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.put(
            "/api/v1/tags/tickets/999999/tags",
            json={"tag_ids": []},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_user_cannot_set_tags(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        user = await _create_user(client, admin, uid)
        type_id = await _create_ticket_type(client, admin, f"UT{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "User tag test")

        r = await client.put(
            f"/api/v1/tags/tickets/{ticket['id']}/tags",
            json={"tag_ids": []},
            headers=user["headers"],
        )
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Ticket Notes
# ---------------------------------------------------------------------------

class TestTicketNotes:
    async def test_create_note(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"NT{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Note ticket")

        r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/notes",
            json={"body": "Личная заметка агента"},
            headers=admin,
        )
        assert r.status_code == 201
        assert r.json()["body"] == "Личная заметка агента"

    async def test_list_own_notes_only(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        agent = await _create_agent(client, admin, uid)
        type_id = await _create_ticket_type(client, admin, f"LN{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Notes isolation",
                                      department_id=agent["dept_id"])

        await client.post(f"/api/v1/tickets/{ticket['id']}/notes",
                          json={"body": "Admin note"}, headers=admin)
        await client.post(f"/api/v1/tickets/{ticket['id']}/notes",
                          json={"body": "Agent note"}, headers=agent["headers"])

        r_admin = await client.get(f"/api/v1/tickets/{ticket['id']}/notes", headers=admin)
        r_agent = await client.get(f"/api/v1/tickets/{ticket['id']}/notes", headers=agent["headers"])

        assert r_admin.status_code == 200
        assert r_agent.status_code == 200
        assert all(n["body"] == "Admin note" for n in r_admin.json())
        assert all(n["body"] == "Agent note" for n in r_agent.json())

    async def test_update_own_note(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"UN{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Update note")

        note_r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/notes",
            json={"body": "Старая заметка"},
            headers=admin,
        )
        note_id = note_r.json()["id"]

        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}/notes/{note_id}",
            json={"body": "Обновлённая заметка"},
            headers=admin,
        )
        assert r.status_code == 200
        assert r.json()["body"] == "Обновлённая заметка"

    async def test_cannot_update_others_note(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        agent = await _create_agent(client, admin, uid)
        type_id = await _create_ticket_type(client, admin, f"CON{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Others note")

        note_r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/notes",
            json={"body": "Admin note"},
            headers=admin,
        )
        note_id = note_r.json()["id"]

        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}/notes/{note_id}",
            json={"body": "Hack"},
            headers=agent["headers"],
        )
        assert r.status_code == 403

    async def test_delete_own_note(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"DN{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Delete note")

        note_r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/notes",
            json={"body": "Заметка для удаления"},
            headers=admin,
        )
        note_id = note_r.json()["id"]

        r = await client.delete(f"/api/v1/tickets/{ticket['id']}/notes/{note_id}", headers=admin)
        assert r.status_code == 204

        r2 = await client.get(f"/api/v1/tickets/{ticket['id']}/notes", headers=admin)
        ids = [n["id"] for n in r2.json()]
        assert note_id not in ids

    async def test_admin_can_delete_others_note(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        agent = await _create_agent(client, admin, uid)
        type_id = await _create_ticket_type(client, admin, f"ADN{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Admin del note",
                                      department_id=agent["dept_id"])

        note_r = await client.post(
            f"/api/v1/tickets/{ticket['id']}/notes",
            json={"body": "Agent note"},
            headers=agent["headers"],
        )
        note_id = note_r.json()["id"]

        r = await client.delete(
            f"/api/v1/tickets/{ticket['id']}/notes/{note_id}",
            headers=admin,
        )
        assert r.status_code == 204

    async def test_user_cannot_access_notes(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        user = await _create_user(client, admin, uid)
        type_id = await _create_ticket_type(client, admin, f"UNA{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "User no notes")

        r = await client.get(f"/api/v1/tickets/{ticket['id']}/notes", headers=user["headers"])
        assert r.status_code == 403

    async def test_note_not_found(self, client: AsyncClient):
        uid = uuid.uuid4().hex[:6]
        admin = await _auth(client)
        type_id = await _create_ticket_type(client, admin, f"NNF{uid}")
        prio_id = await _get_priority_id(client, admin)
        ticket = await _create_ticket(client, admin, type_id, prio_id, "Note NF")

        r = await client.put(
            f"/api/v1/tickets/{ticket['id']}/notes/999999",
            json={"body": "x"},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_ticket_not_found_for_note(self, client: AsyncClient):
        admin = await _auth(client)
        r = await client.post(
            "/api/v1/tickets/999999/notes",
            json={"body": "x"},
            headers=admin,
        )
        assert r.status_code == 404

    async def test_requires_auth_notes(self, client: AsyncClient):
        r = await client.get("/api/v1/tickets/1/notes")
        assert r.status_code in (401, 403)
