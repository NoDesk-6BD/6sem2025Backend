from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .authentication.services import AuthenticationService
from .authentication.hashers import Argon2PasswordHasher
from .authentication.protocols import PasswordHasherProtocol, TokenIssuerProtocol
from .authentication.routers import authentication_router
from .authentication.tokens import JWTTokenIssuer
from .core.database.protocols import SQLAlchemySettingsProtocol, MongoSettingsProtocol
from .core.database.session import get_session
from .core.di import provider_for
from .core.settings import Settings
from .users.protocols import PasswordHasherProtocol as UsersPasswordHasherProtocol

# Routers
from .users.routers import users_router
from .dashboard.routers import dashboard_router
from .terms.routers import terms_router
from .kpi.routers import kpi_router

from fastapi.middleware.cors import CORSMiddleware

origins = ["http://127.0.0.1:8000", "http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.title = settings.APP_NAME
    app.version = settings.APP_VERSION

    # Dependency Injection
    app.dependency_overrides[provider_for(Settings)] = lambda: settings

    # Database and ORM
    if settings.APP_ENVIRONMENT != "testing":
        app.dependency_overrides[provider_for(SQLAlchemySettingsProtocol)] = lambda: settings
        app.dependency_overrides[provider_for(MongoSettingsProtocol)] = lambda: settings
        app.dependency_overrides[provider_for(AsyncSession)] = get_session

    # Password Hasher
    password_hasher = Argon2PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
    app.dependency_overrides[provider_for(UsersPasswordHasherProtocol)] = lambda: password_hasher
    app.dependency_overrides[provider_for(PasswordHasherProtocol)] = lambda: password_hasher

    # Token Issuer
    token_issuer = JWTTokenIssuer(secret=settings.APP_SECRET.get_secret_value())
    app.dependency_overrides[provider_for(TokenIssuerProtocol)] = lambda: token_issuer

    # Authentication
    app.dependency_overrides[provider_for(AuthenticationService)] = AuthenticationService

    # Bootstrap Administrator
    if settings.APP_ENVIRONMENT != "testing":
        async for session in get_session(settings):
            from .users.models import User

            result = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
            admin = result.scalar_one_or_none()
            if admin:
                break
            admin = User(
                email=settings.ADMIN_EMAIL,
                encrypted_password=password_hasher.hash(settings.ADMIN_PASSWORD.get_secret_value()),
                cpf=settings.ADMIN_CPF,
                full_name="Administrator",
                vip=True,
                active=True,
            )
            session.add(admin)
            await session.commit()

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Routers
app.include_router(users_router)
app.include_router(authentication_router)
app.include_router(dashboard_router)
app.include_router(terms_router)
app.include_router(kpi_router)
