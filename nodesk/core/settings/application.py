from typing import Literal

from pydantic import Field, SecretStr

from .base import BaseSettings


class ApplicationSettings(BaseSettings):
    APP_NAME: str = Field()
    APP_VERSION: str = Field()
    APP_ENVIRONMENT: Literal["development", "production", "testing"] = Field()
    APP_SECRET: SecretStr = Field()
