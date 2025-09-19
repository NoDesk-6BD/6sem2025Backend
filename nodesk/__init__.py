from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .authentication.hashers import Argon2PasswordHasher
from .authentication.protocols import PasswordHasherProtocol, TokenIssuerProtocol
from .authentication.routers import authentication_router
from .authentication.tokens import JWTTokenIssuer
from .core.database.protocols import SQLAlchemySettingsProtocol
from .core.database.session import get_session
from .core.di import provider_for
from .core.settings import Settings
from .users.protocols import PasswordHasherProtocol as UsersPasswordHasherProtocol

# Routers
from .users.routers import users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.title = settings.APP_NAME
    app.version = settings.APP_VERSION

    # Dependency Injection
    app.dependency_overrides[provider_for(Settings)] = lambda: settings

    # Database and ORM
    app.dependency_overrides[provider_for(SQLAlchemySettingsProtocol)] = (
        lambda: settings
    )
    app.dependency_overrides[provider_for(AsyncSession)] = get_session

    # Password Hasher
    password_hasher = Argon2PasswordHasher(
        time_cost=3, memory_cost=65536, parallelism=2
    )
    app.dependency_overrides[provider_for(UsersPasswordHasherProtocol)] = (
        lambda: password_hasher
    )
    app.dependency_overrides[provider_for(PasswordHasherProtocol)] = (
        lambda: password_hasher
    )

    # Token Issuer
    token_issuer = JWTTokenIssuer(secret=settings.APP_SECRET.get_secret_value())
    app.dependency_overrides[provider_for(TokenIssuerProtocol)] = lambda: token_issuer

    # Bootstrap Administrator
    async for session in get_session(settings):
        from .users.models import User

        result = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()
        if admin:
            break
        admin = User(
            email=settings.ADMIN_EMAIL,
            encrypted_password=password_hasher.hash(
                settings.ADMIN_PASSWORD.get_secret_value()
            ),
            cpf=settings.ADMIN_CPF,
            full_name="Administrator",
            vip=True,
            active=True,
        )
        session.add(admin)
        await session.commit()

    # Routers
    @app.get("/")
    def root(
        settings: Annotated[Settings, Depends(provider_for(Settings))],
    ) -> dict[str, str]:
        return {"service": settings.APP_NAME, "version": settings.APP_VERSION}

    @app.get("/health")
    def health(
        settings: Annotated[Settings, Depends(provider_for(Settings))],
    ) -> dict[str, str]:
        return {"status": "ok", "environment": settings.APP_ENVIRONMENT}

    app.include_router(users_router)
    app.include_router(authentication_router)

    yield


app = FastAPI(lifespan=lifespan)
