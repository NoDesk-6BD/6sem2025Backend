from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    # SQL Server
    MSSQL_HOST: str = Field(default="localhost")
    MSSQL_PORT: int = Field(default=1433)
    MSSQL_USER: str = Field(default="sa")
    MSSQL_PASSWORD: str = Field(default="nodesk")
    MSSQL_DATABASE: str = Field(default="NoDesk")
    MSSQL_DRIVER: str = Field(default="ODBC Driver 18 for SQL Server")
    MSSQL_ENCRYPT: bool = Field(default=True)
    MSSQL_TRUST_SERVER_CERTIFICATE: bool = Field(default=True)

    # MongoDB
    MONGO_URI: str = Field(default="mongodb://localhost:27017")
    MONGO_DB: str = Field(default="nodesk")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> URL:
        query = {"driver": self.MSSQL_DRIVER}
        if self.MSSQL_ENCRYPT:
            query["Encrypt"] = "yes"
        if self.MSSQL_TRUST_SERVER_CERTIFICATE:
            query["TrustServerCertificate"] = "yes"

        return URL.create(
            drivername="mssql+pyodbc",
            username=self.MSSQL_USER,
            password=self.MSSQL_PASSWORD,
            host=self.MSSQL_HOST,
            port=self.MSSQL_PORT,
            database=self.MSSQL_DATABASE,
            query=query,
        )

    @property
    def SQLALCHEMY_ECHO(self):
        return True
