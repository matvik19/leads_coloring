"""
FastStream роутер для healthcheck.
"""

from typing import Dict, Any

from faststream.rabbit import RabbitRouter, RabbitQueue

from app.core.broker.config import QueueNames
from app.core.logging import logger


health_router = RabbitRouter()


@health_router.subscriber(
    RabbitQueue(QueueNames.HEALTH, durable=True)
)
async def handle_health_check(data: dict) -> Dict[str, Any]:
    """
    Health check endpoint для проверки работоспособности воркера.

    Args:
        data: Данные из RabbitMQ сообщения (может быть пустым)

    Returns:
        Dict со статусом сервиса
    """
    logger.debug("Health check запрос")

    return {
        "status": "ok",
        "service": "leads-coloring"
    }
