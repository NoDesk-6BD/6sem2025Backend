from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..di import provider_for
from .protocols import SQLAlchemySettingsProtocol, MongoSettingsProtocol

# Dependencies
SQLAlchemySettings = Annotated[SQLAlchemySettingsProtocol, Depends(provider_for(SQLAlchemySettingsProtocol))]
MongoSettings = Annotated[MongoSettingsProtocol, Depends(provider_for(MongoSettingsProtocol))]

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

async def get_mongo_db(
    mongo_settings: MongoSettings,
) -> AsyncIterator[AsyncIOMotorDatabase]:
    client = AsyncIOMotorClient(mongo_settings.MONGO_URI)
    db = client[mongo_settings.MONGO_DB]
    try:
        yield db
    finally:
        client.close()