import os
from collections.abc import AsyncIterator

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from nodesk import app
from nodesk.core.di import provider_for
from nodesk.users.models import table_registry


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _env() -> AsyncIterator[None]:
    from dotenv import load_dotenv

    load_dotenv(".env.example")
    os.environ.update({"APP_ENVIRONMENT": "testing"})

    yield


@pytest_asyncio.fixture(scope="session")
async def _sqlite_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def _sessionmaker(
    _sqlite_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=_sqlite_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(
    _sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def session_dep() -> AsyncIterator[AsyncSession]:
        async with _sessionmaker() as s:
            yield s

    app.dependency_overrides[provider_for(AsyncSession)] = session_dep

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
