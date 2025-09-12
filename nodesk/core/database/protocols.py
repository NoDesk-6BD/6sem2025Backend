from typing import Protocol


class DatabaseSettings(Protocol):
    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_ECHO: bool


class Model(Protocol):
    __tablename__: str
