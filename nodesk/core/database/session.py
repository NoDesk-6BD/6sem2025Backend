from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .protocols import DatabaseSettings


async def provide_session(settings: DatabaseSettings) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        echo=settings.SQLALCHEMY_ECHO,
    )
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session
