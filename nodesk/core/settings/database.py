from pydantic import Field, SecretStr

from .base import BaseSettings


class DatabaseSettings(BaseSettings):
    DB_HOST_POSTGRES: str = Field()
    DB_PORT_POSTGRES: int = Field()
    DB_USER_POSTGRES: str = Field()
    DB_PASS_POSTGRES: SecretStr = Field()
    DB_NAME_POSTGRES: str = Field()
