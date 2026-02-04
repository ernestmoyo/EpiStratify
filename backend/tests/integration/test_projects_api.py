"""Integration tests for projects API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProjectsAPI:
    async def test_create_project(self, authenticated_client: AsyncClient):
        response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "name": "Ghana SNT 2025",
                "country": "Ghana",
                "year": 2025,
                "description": "Test project",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Ghana SNT 2025"
        assert data["country"] == "Ghana"
        assert data["year"] == 2025
        assert data["status"] == "draft"

    async def test_list_projects(self, authenticated_client: AsyncClient):
        # Create a project first
        await authenticated_client.post(
            "/api/v1/projects",
            json={
                "name": "Test Project",
                "country": "Tanzania",
                "year": 2025,
            },
        )

        response = await authenticated_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_project(self, authenticated_client: AsyncClient):
        create_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "name": "Get Test",
                "country": "Kenya",
                "year": 2025,
            },
        )
        project_id = create_response.json()["id"]

        response = await authenticated_client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    async def test_update_project(self, authenticated_client: AsyncClient):
        create_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "name": "Update Test",
                "country": "Nigeria",
                "year": 2025,
            },
        )
        project_id = create_response.json()["id"]

        response = await authenticated_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_archive_project(self, authenticated_client: AsyncClient):
        create_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "name": "Archive Test",
                "country": "Mali",
                "year": 2025,
            },
        )
        project_id = create_response.json()["id"]

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project_id}"
        )
        assert response.status_code == 204

    async def test_create_project_initializes_workflow(
        self, authenticated_client: AsyncClient
    ):
        create_response = await authenticated_client.post(
            "/api/v1/projects",
            json={
                "name": "Workflow Init Test",
                "country": "Senegal",
                "year": 2025,
            },
        )
        project_id = create_response.json()["id"]

        response = await authenticated_client.get(
            f"/api/v1/projects/{project_id}/workflow"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["steps"]) == 10
        assert data["overall_progress"] == 0

    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401
