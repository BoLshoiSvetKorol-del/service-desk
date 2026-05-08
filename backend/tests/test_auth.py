import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
async def create_admin(db_session: AsyncSession):
    from app.services.auth_service import seed_admin
    await seed_admin(db_session)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

async def _login(client: AsyncClient, username="admin", password="changeme") -> dict:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return r


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    async def test_success(self, client: AsyncClient):
        r = await _login(client)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    async def test_wrong_password(self, client: AsyncClient):
        r = await _login(client, password="wrong")
        assert r.status_code == 401

    async def test_unknown_user(self, client: AsyncClient):
        r = await _login(client, username="nobody")
        assert r.status_code == 401

    async def test_empty_body(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/login", json={})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    async def test_success(self, client: AsyncClient):
        login_r = await _login(client)
        refresh_token = login_r.json()["refresh_token"]

        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_invalid_token(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "bad.token.value"})
        assert r.status_code == 401

    async def test_access_token_rejected(self, client: AsyncClient):
        login_r = await _login(client)
        access_token = login_r.json()["access_token"]

        # Нельзя использовать access-token как refresh-token
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestMe:
    async def test_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 403

    async def test_returns_current_user(self, client: AsyncClient):
        token = (await _login(client)).json()["access_token"]
        r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "admin"
        assert r.json()["role"] == "admin"

    async def test_invalid_token(self, client: AsyncClient):
        r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    async def test_success(self, client: AsyncClient):
        data = (await _login(client)).json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        r = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert r.status_code == 204

    async def test_refresh_blocked_after_logout(self, client: AsyncClient):
        data = (await _login(client)).json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Выход
        await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Попытка обновить токен после выхода — должна вернуть 401
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 401

    async def test_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/logout", json={"refresh_token": "any"})
        assert r.status_code == 403
