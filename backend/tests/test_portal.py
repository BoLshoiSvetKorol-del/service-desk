"""Tests for Mission 17: register / verify-email endpoints."""
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


async def _admin_headers(client: AsyncClient) -> dict:
    r = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "changeme"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestRegister:
    async def test_register_creates_user(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={
            "email": "portal_user@example.com",
            "password": "portal123",
            "full_name": "Portal User One",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "portal_user@example.com"
        assert data["role"] == "user"
        assert data["is_email_verified"] is False

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "password": "dup123",
            "full_name": "Dup User",
        })
        r = await client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "password": "dup123",
            "full_name": "Dup User 2",
        })
        assert r.status_code == 409

    async def test_register_short_password(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "abc",
            "full_name": "Short",
        })
        assert r.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "valid_pass",
            "full_name": "Bad",
        })
        assert r.status_code == 422

    async def test_registered_user_can_login_by_email(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "logintest@example.com",
            "password": "testpass",
            "full_name": "Login Test",
        })
        r = await client.post("/api/v1/auth/login", json={
            "username": "logintest@example.com",
            "password": "testpass",
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    async def test_auto_username_uniqueness(self, client: AsyncClient):
        """Two users with same email prefix get unique usernames."""
        await client.post("/api/v1/auth/register", json={
            "email": "user@domainA.com",
            "password": "pass123",
            "full_name": "User A",
        })
        r = await client.post("/api/v1/auth/register", json={
            "email": "user@domainB.com",
            "password": "pass123",
            "full_name": "User B",
        })
        assert r.status_code == 201


class TestVerifyEmail:
    async def test_invalid_token_returns_400(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/verify-email?token=invalid_token_xyz")
        assert r.status_code == 400

    async def test_resend_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/resend-verification")
        assert r.status_code == 403

    async def test_resend_unverified_user(self, client: AsyncClient):
        await client.post("/api/v1/auth/register", json={
            "email": "resend_test@example.com",
            "password": "resendpass",
            "full_name": "Resend Test",
        })
        login_r = await client.post("/api/v1/auth/login", json={
            "username": "resend_test@example.com", "password": "resendpass"
        })
        headers = {"Authorization": f"Bearer {login_r.json()['access_token']}"}
        r = await client.post("/api/v1/auth/resend-verification", headers=headers)
        assert r.status_code == 204

    async def test_resend_already_verified_returns_400(self, client: AsyncClient):
        admin_h = await _admin_headers(client)
        r = await client.post("/api/v1/auth/resend-verification", headers=admin_h)
        assert r.status_code == 400

    async def test_admin_created_user_is_verified(self, client: AsyncClient):
        admin_h = await _admin_headers(client)
        r = await client.post("/api/v1/users", json={
            "email": "adminmade@example.com",
            "username": "adminmade1",
            "password": "adminmade",
            "full_name": "Admin Made",
            "role": "user",
        }, headers=admin_h)
        assert r.status_code == 201
        assert r.json()["is_email_verified"] is True
