"""
Основной FastStream брокер для запуска воркера.

Запуск:
    faststream run app.broker_app:app --workers 1
"""

from faststream import FastStream

from app.core.broker.app import broker
from app.core.logging import setup_logging, logger

# Настраиваем логирование для воркера
setup_logging(service_name="leads-coloring-worker", environment="production")

# Создаем FastStream приложение
app = FastStream(broker)


@app.on_startup
async def startup_hook():
    """Хук выполняется при старте воркера."""
    logger.info("FastStream воркер запускается...")
    logger.info("Подключение к RabbitMQ...")


@app.after_startup
async def after_startup_hook():
    """Хук выполняется после успешного старта."""
    logger.info("FastStream воркер успешно запущен")
    logger.info("Слушаем очереди RabbitMQ...")


@app.on_shutdown
async def shutdown_hook():
    """Хук выполняется при остановке воркера."""
    logger.info("FastStream воркер останавливается...")


@app.after_shutdown
async def after_shutdown_hook():
    """Хук выполняется после остановки."""
    logger.info("FastStream воркер успешно остановлен")
