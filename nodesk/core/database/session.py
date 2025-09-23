from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..di import provider_for
from .protocols import SQLAlchemySettingsProtocol

# Dependencies
SQLAlchemySettings = Annotated[SQLAlchemySettingsProtocol, Depends(provider_for(SQLAlchemySettingsProtocol))]


async def get_session(
    database_settings: SQLAlchemySettings,
) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        database_settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,
        echo=database_settings.SQLALCHEMY_ECHO,
        connect_args={"options": "-c timezone=UTC"},
    )
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session
    await engine.dispose()
