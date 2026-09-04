import pytest

@pytest.mark.asyncio
async def test_create_project(client):
    response = await client.post("/api/projects", json={"name": "Bio Textbook", "description": "Grade 10 Biology"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bio Textbook"
    assert data["status"] == "created"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_projects(client):
    await client.post("/api/projects", json={"name": "Project 1"})
    await client.post("/api/projects", json={"name": "Project 2"})
    response = await client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_get_project_not_found(client):
    response = await client.get("/api/projects/nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_project(client):
    resp = await client.post("/api/projects", json={"name": "To Delete"})
    project_id = resp.json()["id"]
    del_resp = await client.delete(f"/api/projects/{project_id}")
    assert del_resp.status_code == 204
    get_resp = await client.get(f"/api/projects/{project_id}")
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_create_project_empty_name(client):
    response = await client.post("/api/projects", json={"name": ""})
    assert response.status_code == 422
