from typing import Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator, ValidationInfo


class DBConfig(BaseSettings):
    """
    Конфигурация PostgreSQL
    """

    HOST: str = "localhost"
    USER: str = "postgres"
    PASSWORD: str = "password"
    DATABASE: str = "leads_coloring"
    PORT: int = 5432

    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: ValidationInfo) -> Any:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.data.get("USER"),
            password=values.data.get("PASSWORD"),
            host=values.data.get("HOST", "localhost"),
            port=values.data.get("PORT"),
            path=f"{values.data.get('DATABASE')}",
        )

    @property
    def sqlalchemy_async_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{self.DATABASE}"
        )

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")


class RabbitConfig(BaseSettings):
    """
    Конфигурация RabbitMQ
    """

    HOST: str = "broker"
    PORT: int = 5672
    USER: str = "guest"
    PASS: str = "guest"
    VHOST: str = "/"

    @property
    def rabbitmq_uri(self) -> str:
        return f"amqp://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.VHOST}"

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_", env_file=".env", extra="ignore")


class GunicornConfig(BaseSettings):
    """
    Конфигурация Gunicorn
    """

    WORKERS: int = 1
    BIND_IP: str = "0.0.0.0"
    PORT: int = 8000
    MAX_REQUESTS: int = 1000
    MAX_REQUESTS_JITTER: int = 250

    GUNICORN_PID_LOCATION: str = "/tmp/gunicorn.pid"

    model_config = SettingsConfigDict(env_prefix="WEB_", env_file=".env", extra="ignore")


class WorkerConfig(BaseSettings):
    """
    Конфигурация FastStream воркера
    """

    WORKERS: int = 1
    MAX_TASKS_PER_CHILD: int = 2500
    PREFETCH_COUNT: int = 10

    model_config = SettingsConfigDict(env_prefix="WORKER_", env_file=".env", extra="ignore")


class AmoCRMConfig(BaseSettings):
    """
    Конфигурация AmoCRM
    """

    CLIENT_SECRET: str = ""
    CLIENT_ID: str = ""
    REDIRECT_URL: str = ""

    # Rate limiting settings
    RATE_LIMIT: float = 6.0  # Запросов в секунду
    RATE_BURST: int = 6  # Burst capacity

    model_config = SettingsConfigDict(env_prefix="AMOCRM_", env_file=".env", extra="ignore")


class AppConfig(BaseSettings):
    """
    Конфигурация приложения
    """

    VERSION: str = "0.1.0"
    PROJECT_DESC: str = "AmoCRM Leads Coloring Widget Backend"
    PROJECT_NAME: str = "Leads Coloring Service"

    OPENAPI_PATH: str = "/openapi.json"
    NAMESPACE: str = ""

    LOGLEVEL: str = "INFO"
    TZ: str = "Europe/Moscow"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")


class Settings(BaseSettings):
    """
    Контейнер всех настроек приложения
    """

    db_cfg: DBConfig = DBConfig()
    rabbit_cfg: RabbitConfig = RabbitConfig()
    web_cfg: GunicornConfig = GunicornConfig()
    worker_cfg: WorkerConfig = WorkerConfig()
    amocrm_cfg: AmoCRMConfig = AmoCRMConfig()
    app_cfg: AppConfig = AppConfig()


config = Settings()
