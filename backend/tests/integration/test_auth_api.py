"""Integration tests for auth API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthAPI:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "full_name": "Test User",
                "organization": "Test Org",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "email": "dup@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        }
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "testpassword123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test2@example.com",
                "password": "short",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "testpassword123",
                "full_name": "Login User",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrong@example.com",
                "password": "testpassword123",
                "full_name": "User",
            },
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_get_me_authenticated(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "testpassword123",
                "full_name": "Refresh User",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "testpassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
