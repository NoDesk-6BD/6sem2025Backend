from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.settings import AppSettings, provide_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = provide_settings()
    app.title = settings.APP_NAME
    app.version = settings.APP_VERSION
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root(settings: AppSettings) -> dict[str, str]:
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
def health(settings: AppSettings) -> dict[str, str]:
    return {"status": "ok", "environment": settings.APP_ENVIRONMENT}
