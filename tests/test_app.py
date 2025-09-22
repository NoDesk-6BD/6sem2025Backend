import pytest

from nodesk import app


@pytest.mark.asyncio
async def test_root_and_health(client):
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == app.title
    assert data["version"] == app.version

    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "environment" in data


@pytest.mark.asyncio
async def test_docs_and_openapi(client):
    r = await client.get("/docs")
    assert r.status_code == 200
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema and "/users/" in schema["paths"]
