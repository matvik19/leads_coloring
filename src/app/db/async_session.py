import asyncio
import subprocess
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncConnection,
)
import asyncpg
from app.core.settings import config
from app.core.logging import logger


async_engine = create_async_engine(
    str(config.db_cfg.SQLALCHEMY_DATABASE_URI),
    echo=False,
    pool_pre_ping=True,
    pool_size=30,
    max_overflow=25,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_conn() -> AsyncConnection:
    async with async_engine.connect() as conn:
        yield conn


async def wait_for_db():
    """Ожидаем доступности базы данных перед запуском сервиса."""
    retries = 10
    while retries:
        try:
            conn = await asyncpg.connect(
                user=config.db_cfg.USER,
                password=config.db_cfg.PASSWORD,
                database=config.db_cfg.DATABASE,
                host=config.db_cfg.HOST,
                port=config.db_cfg.PORT,
            )
            await conn.close()
            logger.info("Database is ready.")
            return
        except Exception as e:
            logger.warning(f"Database not ready, retrying... {retries} attempts left. Error: {e}")
            retries -= 1
            await asyncio.sleep(2)
    logger.error("Database is not available, exiting.")
    exit(1)


async def run_migrations():
    """Запускаем Alembic миграции."""
    import os
    logger.info("Running database migrations...")
    # Определяем путь к директории src где находится alembic.ini
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    subprocess.run("alembic upgrade head", shell=True, check=True, cwd=src_dir)
    logger.info("Migrations completed.")
