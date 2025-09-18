from pydantic import Field, SecretStr

from .base import BaseSettings


class AdministratorSettings(BaseSettings):
    ADMIN_EMAIL: str = Field()
    ADMIN_PASSWORD: SecretStr = Field()
    ADMIN_CPF: str = Field()
