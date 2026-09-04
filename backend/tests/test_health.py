import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TactileEd"
    assert "version" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_health_returns_utc_timestamp(client):
    response = await client.get("/health")
    data = response.json()
    # Timestamp should be ISO format with UTC indicator
    assert "T" in data["timestamp"]
