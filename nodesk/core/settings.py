from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import Field, SecretStr, ValidationError, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # Application
    APP_NAME: str = Field()
    APP_VERSION: str = Field()
    APP_ENVIRONMENT: Literal["development", "production", "testing"] = Field()
    APP_SECRET: SecretStr = Field()

    # Database
    DB_HOST: str = Field()
    DB_PORT: int = Field()
    DB_USER: str = Field()
    DB_PASS: SecretStr = Field()
    DB_NAME: str = Field()

    # SQLAlchemy
    @computed_field(return_type=bool)
    def SQLALCHEMY_ECHO(self) -> bool:
        return self.APP_ENVIRONMENT == "development"

    @computed_field(return_type=str)
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        url = URL.create(
            drivername="postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASS.get_secret_value(),
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )
        return url.render_as_string(hide_password=False)

    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


@lru_cache(maxsize=1)
def provide_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        missing = [
            "/".join(map(str, err["loc"]))
            for err in e.errors()
            if err["type"] == "missing"
        ]
        raise RuntimeError(
            "Variáveis obrigatórias ausentes no .env ou no ambiente: "
            f"{', '.join(missing)}"
        ) from e


AppSettings = Annotated[Settings, Depends(provide_settings)]
