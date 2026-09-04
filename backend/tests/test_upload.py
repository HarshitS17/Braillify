import pytest
import io
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"


@pytest.mark.asyncio
async def test_upload_png(client):
    # Create project first
    proj_resp = await client.post("/api/projects", json={"name": "Upload Test"})
    project_id = proj_resp.json()["id"]
    
    fixture = FIXTURE_DIR / "simple_shapes.png"
    if not fixture.exists():
        pytest.skip("Fixture not generated")
    
    with open(fixture, "rb") as f:
        resp = await client.post(
            f"/api/projects/{project_id}/pages",
            files={"file": ("test.png", f, "image/png")},
        )
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == project_id
    assert data["format"] == "png"
    assert data["width"] == 800
    assert data["height"] == 600
    assert "page_id" in data


@pytest.mark.asyncio
async def test_upload_unsupported_format(client):
    proj_resp = await client.post("/api/projects", json={"name": "Test"})
    project_id = proj_resp.json()["id"]
    
    resp = await client.post(
        f"/api/projects/{project_id}/pages",
        files={"file": ("test.bmp", b"fake content", "image/bmp")},
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_upload_empty_file(client):
    proj_resp = await client.post("/api/projects", json={"name": "Test"})
    project_id = proj_resp.json()["id"]
    
    resp = await client.post(
        f"/api/projects/{project_id}/pages",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_to_nonexistent_project(client):
    resp = await client.post(
        "/api/projects/nonexistent/pages",
        files={"file": ("test.png", b"content", "image/png")},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_pages(client):
    proj_resp = await client.post("/api/projects", json={"name": "List Pages Test"})
    project_id = proj_resp.json()["id"]
    
    fixture = FIXTURE_DIR / "simple_shapes.png"
    if not fixture.exists():
        pytest.skip("Fixture not generated")
    
    with open(fixture, "rb") as f:
        await client.post(
            f"/api/projects/{project_id}/pages",
            files={"file": ("test.png", f, "image/png")},
        )
    
    resp = await client.get(f"/api/projects/{project_id}/pages")
    assert resp.status_code == 200
    pages = resp.json()
    assert len(pages) >= 1
