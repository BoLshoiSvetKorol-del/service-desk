import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
async def create_admin(db_session: AsyncSession):
    from app.services.auth_service import seed_admin
    await seed_admin(db_session)


async def _login(client: AsyncClient, username="admin", password="changeme") -> str:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


async def _auth(client: AsyncClient, username="admin", password="changeme") -> dict:
    token = await _login(client, username, password)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

class TestDepartments:
    async def test_create_department(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.post("/api/v1/departments", json={"name": "IT", "description": "IT отдел"}, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "IT"
        assert data["description"] == "IT отдел"
        assert "id" in data

    async def test_create_duplicate_department(self, client: AsyncClient):
        headers = await _auth(client)
        await client.post("/api/v1/departments", json={"name": "HR"}, headers=headers)
        r = await client.post("/api/v1/departments", json={"name": "HR"}, headers=headers)
        assert r.status_code == 409

    async def test_list_departments(self, client: AsyncClient):
        headers = await _auth(client)
        await client.post("/api/v1/departments", json={"name": "Finance"}, headers=headers)
        r = await client.get("/api/v1/departments", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        names = [d["name"] for d in r.json()]
        assert "Finance" in names

    async def test_get_department_with_agents(self, client: AsyncClient):
        headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "Support"}, headers=headers)
        dept_id = dept_r.json()["id"]

        r = await client.get(f"/api/v1/departments/{dept_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["id"] == dept_id
        assert "agents" in r.json()

    async def test_get_department_not_found(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/departments/99999", headers=headers)
        assert r.status_code == 404

    async def test_update_department(self, client: AsyncClient):
        headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "OldName"}, headers=headers)
        dept_id = dept_r.json()["id"]

        r = await client.put(f"/api/v1/departments/{dept_id}", json={"name": "NewName"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["name"] == "NewName"

    async def test_delete_empty_department(self, client: AsyncClient):
        headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "ToDelete"}, headers=headers)
        dept_id = dept_r.json()["id"]

        r = await client.delete(f"/api/v1/departments/{dept_id}", headers=headers)
        assert r.status_code == 204

    async def test_departments_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/departments")
        assert r.status_code == 403

    async def test_create_department_requires_admin(self, client: AsyncClient):
        admin_headers = await _auth(client)
        # Создаём агента
        dept_r = await client.post("/api/v1/departments", json={"name": "AgentDept"}, headers=admin_headers)
        dept_id = dept_r.json()["id"]
        await client.post(
            "/api/v1/users",
            json={
                "username": "agent1", "email": "agent1@test.com",
                "password": "secret1", "full_name": "Agent One",
                "role": "agent", "department_id": dept_id,
            },
            headers=admin_headers,
        )
        agent_token = await _login(client, "agent1", "secret1")
        agent_headers = {"Authorization": f"Bearer {agent_token}"}

        r = await client.post("/api/v1/departments", json={"name": "Blocked"}, headers=agent_headers)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class TestUsers:
    async def test_get_me(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/users/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    async def test_update_me_full_name(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.put("/api/v1/users/me", json={"full_name": "New Admin Name"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["full_name"] == "New Admin Name"

    async def test_create_user(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.post(
            "/api/v1/users",
            json={
                "username": "newuser", "email": "newuser@test.com",
                "password": "password123", "full_name": "New User",
                "role": "user",
            },
            headers=headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert data["is_active"] is True

    async def test_create_user_duplicate_email(self, client: AsyncClient):
        headers = await _auth(client)
        payload = {
            "username": "dup1", "email": "dup@test.com",
            "password": "pass123", "full_name": "Dup User", "role": "user",
        }
        await client.post("/api/v1/users", json=payload, headers=headers)
        payload["username"] = "dup2"
        r = await client.post("/api/v1/users", json=payload, headers=headers)
        assert r.status_code == 409

    async def test_create_user_duplicate_username(self, client: AsyncClient):
        headers = await _auth(client)
        payload = {
            "username": "sameuser", "email": "u1@test.com",
            "password": "pass123", "full_name": "User", "role": "user",
        }
        await client.post("/api/v1/users", json=payload, headers=headers)
        payload["email"] = "u2@test.com"
        r = await client.post("/api/v1/users", json=payload, headers=headers)
        assert r.status_code == 409

    async def test_list_users_admin_only(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/users", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_list_users_filter_by_role(self, client: AsyncClient):
        headers = await _auth(client)
        r = await client.get("/api/v1/users?role=admin", headers=headers)
        assert r.status_code == 200
        for u in r.json()["items"]:
            assert u["role"] == "admin"

    async def test_list_users_search(self, client: AsyncClient):
        headers = await _auth(client)
        await client.post(
            "/api/v1/users",
            json={
                "username": "searchable_user", "email": "searchable@test.com",
                "password": "pass123", "full_name": "Searchable Person", "role": "user",
            },
            headers=headers,
        )
        r = await client.get("/api/v1/users?search=searchable", headers=headers)
        assert r.status_code == 200
        usernames = [u["username"] for u in r.json()["items"]]
        assert "searchable_user" in usernames

    async def test_get_user_by_id_admin(self, client: AsyncClient):
        headers = await _auth(client)
        create_r = await client.post(
            "/api/v1/users",
            json={
                "username": "user_to_get", "email": "toget@test.com",
                "password": "pass123", "full_name": "Get Me", "role": "user",
            },
            headers=headers,
        )
        user_id = create_r.json()["id"]
        r = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["id"] == user_id

    async def test_update_user(self, client: AsyncClient):
        headers = await _auth(client)
        create_r = await client.post(
            "/api/v1/users",
            json={
                "username": "to_update", "email": "toupdate@test.com",
                "password": "pass123", "full_name": "Original Name", "role": "user",
            },
            headers=headers,
        )
        user_id = create_r.json()["id"]
        r = await client.put(
            f"/api/v1/users/{user_id}",
            json={"full_name": "Updated Name"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated Name"

    async def test_toggle_activate(self, client: AsyncClient):
        headers = await _auth(client)
        create_r = await client.post(
            "/api/v1/users",
            json={
                "username": "to_deactivate", "email": "deact@test.com",
                "password": "pass123", "full_name": "Active User", "role": "user",
            },
            headers=headers,
        )
        user_id = create_r.json()["id"]
        assert create_r.json()["is_active"] is True

        r = await client.patch(f"/api/v1/users/{user_id}/activate", headers=headers)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

        r2 = await client.patch(f"/api/v1/users/{user_id}/activate", headers=headers)
        assert r2.status_code == 200
        assert r2.json()["is_active"] is True

    async def test_cannot_deactivate_self(self, client: AsyncClient):
        headers = await _auth(client)
        me_r = await client.get("/api/v1/users/me", headers=headers)
        admin_id = me_r.json()["id"]

        r = await client.patch(f"/api/v1/users/{admin_id}/activate", headers=headers)
        assert r.status_code == 400

    async def test_regular_user_cannot_list_users(self, client: AsyncClient):
        admin_headers = await _auth(client)
        await client.post(
            "/api/v1/users",
            json={
                "username": "regular_u", "email": "regular@test.com",
                "password": "pass123", "full_name": "Regular", "role": "user",
            },
            headers=admin_headers,
        )
        token = await _login(client, "regular_u", "pass123")
        user_headers = {"Authorization": f"Bearer {token}"}

        r = await client.get("/api/v1/users", headers=user_headers)
        assert r.status_code == 403

    async def test_create_user_with_department(self, client: AsyncClient):
        headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "DevDept"}, headers=headers)
        dept_id = dept_r.json()["id"]

        r = await client.post(
            "/api/v1/users",
            json={
                "username": "devuser", "email": "devuser@test.com",
                "password": "pass123", "full_name": "Dev User",
                "role": "agent", "department_id": dept_id,
            },
            headers=headers,
        )
        assert r.status_code == 201
        assert r.json()["department_id"] == dept_id

    async def test_delete_department_with_users_allowed(self, client: AsyncClient):
        headers = await _auth(client)
        dept_r = await client.post("/api/v1/departments", json={"name": "Temp Dept"}, headers=headers)
        dept_id = dept_r.json()["id"]

        await client.post(
            "/api/v1/users",
            json={
                "username": "indept_user", "email": "indept@test.com",
                "password": "pass123", "full_name": "In Dept", "role": "agent",
                "department_id": dept_id,
            },
            headers=headers,
        )

        # Удаление разрешено (ticket-check добавится в Mission 05)
        r = await client.delete(f"/api/v1/departments/{dept_id}", headers=headers)
        assert r.status_code == 204

        # Отдел больше не существует
        r2 = await client.get(f"/api/v1/departments/{dept_id}", headers=headers)
        assert r2.status_code == 404
