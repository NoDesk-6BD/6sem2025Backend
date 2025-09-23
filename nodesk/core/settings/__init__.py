from .admin import AdministratorSettings
from .application import ApplicationSettings
from .database import DatabaseSettings
from .sqlalchemy import SQLAlchemySettings


class Settings(ApplicationSettings, DatabaseSettings, SQLAlchemySettings, AdministratorSettings): ...
