import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from nodesk import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as asyncClient:
        yield asyncClient
