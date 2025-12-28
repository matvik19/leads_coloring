from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncConnection,
)
from app.core.settings import config


async_engine = create_async_engine(
    str(config.db_cfg.SQLALCHEMY_DATABASE_URI), echo=True, pool_pre_ping=True
)
async_session = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_conn() -> AsyncConnection:
    async with async_engine.connect() as conn:
        yield conn
