from pydantic import Field


from .base import BaseSettings


class MongoSettings(BaseSettings):
    MONGO_URI: str = Field()
    MONGO_DB: str = Field()
