from typing import Literal

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

from typing import ClassVar

class Settings(BaseSettings):
    APP_NAME: str = Field()
    APP_VERSION: str = Field()
    APP_ENVIRONMENT: Literal["development", "production", "testing"] = Field()
    APP_SECRET: SecretStr = Field()

    BASE_DIR: ClassVar[str] = os.path.dirname(os.path.abspath(__file__))

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True
    )


def load_settings() -> Settings:
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
