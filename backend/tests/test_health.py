"""
Tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check functionality."""

    async def test_health_check(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "database" in data
        assert "version" in data
        assert data["status"] in ["healthy", "unhealthy"]

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root API endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "features" in data