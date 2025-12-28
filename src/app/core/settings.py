from typing import Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import MySQLDsn, field_validator, ValidationInfo


class DBConfig(BaseSettings):
    """
    Конфигурация MySQL
    """

    HOST: str = "localhost"
    USER: str = "user"
    PASSWORD: str = "password"
    DATABASE: str = "db"
    PORT: int = 3306

    SQLALCHEMY_DATABASE_URI: Optional[MySQLDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values: ValidationInfo) -> Any:
        return MySQLDsn.build(
            scheme="mysql+asyncmy",
            username=values.data.get("USER"),
            password=values.data.get("PASSWORD"),
            host=values.data.get("HOST", "localhost"),
            port=values.data.get("PORT"),
            path=f"{values.data.get('DATABASE')}",
        )

    @property
    def sqlalchemy_async_database_uri(self) -> str:
        return (
            f"mysql+asyncmy://{self.USER}:{self.PASSWORD}@"
            f"{self.HOST}/{self.DATABASE}?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")


class RedisConfig(BaseSettings):
    """
    Конфигурация Redis
    """

    HOST: str = "cache"
    PORT: int = 6379

    RESULT_INDEX: int = 9
    CACHE_INDEX: int = 0

    @property
    def redis_result_uri(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.RESULT_INDEX}"

    @property
    def redis_cache_uri(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.CACHE_INDEX}"

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")


class RabbitConfig(BaseSettings):
    """
    Конфигурация RabbitMQ
    """

    HOST: str = "broker"
    PORT: int = 5672
    USER: str = "user"
    PASS: str = "password"

    @property
    def rabbitmq_uri(self) -> str:
        return f"amqp://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/"

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


class BackgroundTasksConfig(BaseSettings):
    """
    Конфигурация фоновых задач Taskiq
    """

    WORKERS: int = 1
    MAX_TASKS_PER_CHILD: int = 2500

    model_config = SettingsConfigDict(env_prefix="TASK_", env_file=".env", extra="ignore")


class AppConfig(BaseSettings):
    """
    Конфигурация приложения
    """

    VERSION: str = "0.1.0"
    PROJECT_DESC: str = "Базовый шаблон сервиса"
    PROJECT_NAME: str = "Base Service Template"

    OPENAPI_PATH: str = "/openapi.json"
    NAMESPACE: str = ""

    LOGLEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")


class Settings(BaseSettings):
    """
    Контейнер всех настроек приложения
    """

    db_cfg: DBConfig = DBConfig()
    redis_cfg: RedisConfig = RedisConfig()
    rabbit_cfg: RabbitConfig = RabbitConfig()
    web_cfg: GunicornConfig = GunicornConfig()
    tasks_cfg: BackgroundTasksConfig = BackgroundTasksConfig()
    app_cfg: AppConfig = AppConfig()


config = Settings()
