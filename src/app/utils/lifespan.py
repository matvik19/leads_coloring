from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.async_session import wait_for_db, run_migrations
from app.core.logging import logger
from app.core.broker.app import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом FastAPI (миграции БД + RabbitMQ broker)."""
    await wait_for_db()
    await run_migrations()

    # Запускаем RabbitMQ broker для RPC вызовов из HTTP ручек
    await broker.start()
    logger.info("RabbitMQ broker подключен для RPC вызовов.")

    logger.info("FastAPI приложение готово к работе.")

    try:
        yield
    finally:
        # Останавливаем broker
        await broker.close()
        logger.info("RabbitMQ broker отключен.")
        logger.info("FastAPI приложение останавливается...")
