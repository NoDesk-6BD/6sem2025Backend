from pydantic import computed_field
from sqlalchemy.engine import URL

from .base import BaseSettings


class SQLAlchemySettings(BaseSettings):
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
