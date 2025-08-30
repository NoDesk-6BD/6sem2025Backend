import pytest

from nodesk import app, settings


def test_app_metadata() -> None:
    assert app.title == settings.APP_NAME
    assert app.version == settings.APP_VERSION


@pytest.mark.asyncio
async def test_root_endpoint(client) -> None:
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == app.title
    assert data["version"] == app.version


@pytest.mark.asyncio
async def test_health_endpoint(client) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["environment"] == settings.APP_ENVIRONMENT
