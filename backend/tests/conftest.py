import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.services.storage import StorageService
import sys
from tests import mock_vercel_blob

import vercel.blob

@pytest.fixture(autouse=True)
def patch_vercel_blob(monkeypatch):
    monkeypatch.setattr(vercel.blob, "put", mock_vercel_blob.put)
    monkeypatch.setattr(vercel.blob, "get", mock_vercel_blob.get)
    monkeypatch.setattr(vercel.blob, "delete", mock_vercel_blob.delete)
    monkeypatch.setattr(vercel.blob, "list_objects", mock_vercel_blob.list_objects)
    monkeypatch.setattr(vercel.blob, "head", mock_vercel_blob.head)
    
    mock_vercel_blob.clear()
    yield
    mock_vercel_blob.clear()

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
