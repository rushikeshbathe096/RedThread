import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.mark.anyio
async def test_api_ping():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "redthread-api"


@pytest.mark.anyio
async def test_health_check_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["version"] == "1.0.0"
        assert data["database"] in ("connected", "disconnected")
