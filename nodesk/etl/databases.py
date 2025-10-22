from sqlalchemy import create_engine
from pymongo import MongoClient

from .settings import Settings

settings = Settings()


sqlserver = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=settings.SQLALCHEMY_ECHO)
mongo = MongoClient(settings.MONGO_URI)[settings.MONGO_DB]

print(settings.MONGO_URI)
