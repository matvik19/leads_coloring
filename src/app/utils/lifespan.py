from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.async_session import wait_for_db, run_migrations
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом FastAPI (миграции БД)."""
    await wait_for_db()
    await run_migrations()
    logger.info("FastAPI приложение готово к работе.")

    try:
        yield
    finally:
        logger.info("FastAPI приложение останавливается...")
