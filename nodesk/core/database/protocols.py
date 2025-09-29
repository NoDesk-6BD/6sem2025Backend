from typing import Protocol


class SQLAlchemySettingsProtocol(Protocol):
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_ECHO: bool

class MongoSettingsProtocol(Protocol):
    MONGO_URI: str
    MONGO_DB: str