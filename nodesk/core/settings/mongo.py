from pydantic import computed_field
from pydantic import Field, SecretStr

from sqlalchemy.engine import URL

from .base import BaseSettings


class MongoSettings(BaseSettings):
    MONGO_URI: str = Field()
    MONGO_DB: str = Field()