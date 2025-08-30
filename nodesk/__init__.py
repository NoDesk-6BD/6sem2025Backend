from fastapi import FastAPI

from .core.settings import load_settings

settings = load_settings()
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.APP_ENVIRONMENT}
