from typing import Protocol


class SQLAlchemySettingsProtocol(Protocol):
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_ECHO: bool
