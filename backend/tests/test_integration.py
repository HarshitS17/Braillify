"""
Integration tests — exercises the full API chain.
"""
import pytest
from httpx import AsyncClient

# ── Test 1: Full project creation and health check ──

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TactileEd"

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    response = await client.post("/api/projects", json={
        "name": "Integration Test Project",
        "description": "Testing the full pipeline"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Integration Test Project"
    assert "id" in data

@pytest.mark.asyncio
async def test_project_lifecycle(client: AsyncClient):
    # Create
    resp = await client.post("/api/projects", json={"name": "Lifecycle Test"})
    assert resp.status_code == 201
    project_id = resp.json()["id"]
    
    # List
    resp = await client.get("/api/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert any(p["id"] == project_id for p in projects)
    
    # Get
    resp = await client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == project_id

# ── Test 2: Validation + Export chain ──

@pytest.mark.asyncio
async def test_validation_endpoint_returns_structure(client: AsyncClient):
    # Create a project first
    resp = await client.post("/api/projects", json={"name": "Validation Test"})
    project_id = resp.json()["id"]
    
    # The validate endpoint requires a diagram to exist.
    # Without a real uploaded image we can't create one through the API,
    # so we test that the endpoint returns 404 gracefully for a missing diagram.
    resp = await client.get(f"/api/projects/{project_id}/pages/fake-page/diagrams/fake-diagram/validate")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_export_svg_missing_diagram(client: AsyncClient):
    resp = await client.post("/api/projects", json={"name": "Export Test"})
    project_id = resp.json()["id"]
    
    resp = await client.post(
        f"/api/projects/{project_id}/pages/fake-page/diagrams/fake-diagram/export/svg",
        json={"config": {}}
    )
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_export_pdf_missing_diagram(client: AsyncClient):
    resp = await client.post("/api/projects", json={"name": "PDF Export Test"})
    project_id = resp.json()["id"]
    
    resp = await client.post(
        f"/api/projects/{project_id}/pages/fake-page/diagrams/fake-diagram/export/pdf",
        json={"config": {}}
    )
    assert resp.status_code == 404

# ── Test 3: Workflow endpoint ──

@pytest.mark.asyncio
async def test_workflow_missing_diagram(client: AsyncClient):
    resp = await client.post("/api/projects", json={"name": "Workflow Test"})
    project_id = resp.json()["id"]
    
    resp = await client.post(
        f"/api/projects/{project_id}/pages/fake-page/diagrams/fake-diagram/workflow",
        json={"start_stage": "simplify", "end_stage": "place"}
    )
    assert resp.status_code == 404
