"""
RPC клиент для взаимодействия с внешними сервисами через RabbitMQ.
Использует aio_pika напрямую для надёжного RPC.
"""

import asyncio
import aio_pika
import json
import uuid
import async_timeout
from typing import Dict, Any

from app.core.logging import logger
from app.core.broker.connection import RMQConnectionManager
from app.core.settings import config


# Глобальный менеджер соединений для RPC
_connection_manager: RMQConnectionManager | None = None


def get_connection_manager() -> RMQConnectionManager:
    """Получить или создать глобальный менеджер соединений."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = RMQConnectionManager(config.rabbit_cfg.rabbitmq_uri)
    return _connection_manager


async def close_rpc_connection():
    """Закрыть RPC соединение при завершении приложения."""
    global _connection_manager
    if _connection_manager is not None:
        await _connection_manager.close()
        _connection_manager = None


async def send_rpc_request_and_wait_for_reply(
    subdomain: str,
    client_id: str,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Отправка RPC запроса в сервис токенов и ожидание ответа.

    Args:
        subdomain: Субдомен AmoCRM для получения токенов
        client_id: ID клиента OAuth AmoCRM
        timeout: Таймаут ожидания ответа в секундах (по умолчанию 30)

    Returns:
        Dict с access_token и refresh_token

    Raises:
        TimeoutError: Если не удалось получить ответ за указанное время
        Exception: При других ошибках
    """
    correlation_id = str(uuid.uuid4())
    connection_manager = get_connection_manager()

    try:
        connection = await connection_manager.connect()
        channel = await connection.channel()
    except (asyncio.CancelledError, Exception) as e:
        logger.warning("RPC: Ошибка при создании канала, переподключаемся: %s", e)
        connection = await connection_manager.reconnect()
        channel = await connection.channel()

    reply_queue = await channel.declare_queue(exclusive=True)

    try:
        async with async_timeout.timeout(timeout):
            message = aio_pika.Message(
                body=json.dumps(
                    {"client_id": client_id, "subdomain": subdomain}
                ).encode(),
                correlation_id=correlation_id,
                reply_to=reply_queue.name,
            )

            logger.info("RPC: Отправляем запрос токенов для subdomain=%s", subdomain)

            await channel.default_exchange.publish(
                message, routing_key="tokens_get_user"
            )

            async with reply_queue.iterator() as queue_iter:
                async for msg in queue_iter:
                    async with msg.process():
                        if msg.correlation_id == correlation_id:
                            tokens = json.loads(msg.body.decode())
                            logger.info(
                                "RPC: Получены токены для subdomain=%s", subdomain
                            )
                            return tokens

    except asyncio.TimeoutError:
        logger.error("RPC: Таймаут при запросе токенов для subdomain=%s", subdomain)
        raise

    except asyncio.CancelledError:
        logger.error("RPC: Запрос был отменён для subdomain=%s", subdomain)
        raise

    finally:
        try:
            await reply_queue.delete()
        except Exception:
            pass
        try:
            if not channel.is_closed:
                await channel.close()
        except Exception:
            pass
