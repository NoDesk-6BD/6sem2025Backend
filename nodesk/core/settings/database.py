from pydantic import Field, SecretStr

from .base import BaseSettings


class DatabaseSettings(BaseSettings):
    DB_HOST: str = Field()
    DB_PORT: int = Field()
    DB_USER: str = Field()
    DB_PASS: SecretStr = Field()
    DB_NAME: str = Field()
