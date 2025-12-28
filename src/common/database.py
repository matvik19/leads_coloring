import asyncio
import subprocess
from contextlib import asynccontextmanager
from src.common.log_config import logger


import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.common.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()


engine = create_async_engine(
    DATABASE_URL,
    pool_size=30,
    max_overflow=25,
    echo=False,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def get_async_session_router() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def wait_for_db():
    """Ожидаем доступности базы данных перед запуском сервиса."""
    retries = 10
    while retries:
        try:
            conn = await asyncpg.connect(
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                host=DB_HOST,
                port=DB_PORT,
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
    logger.info("Running database migrations...")
    subprocess.run("alembic upgrade head", shell=True, check=True)
    logger.info("Migrations completed.")
