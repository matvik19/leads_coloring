"""
Health check endpoint через RabbitMQ RPC.
"""
from fastapi import APIRouter

from app.core.logging import logger
from app.core.broker.app import broker
from app.core.broker.config import QueueNames

router = APIRouter(tags=["Health (RPC Proxy)"])

RPC_TIMEOUT = 10.0


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    Проверяет, что worker работает и отвечает на сообщения.
    """
    logger.info("HTTP -> RabbitMQ RPC: health check")

    response = await broker.publish(
        {},
        queue=QueueNames.HEALTH,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    return response
