"""
Менеджер соединений RabbitMQ для RPC запросов.
"""

import aio_pika
from app.core.logging import logger


class RMQConnectionManager:
    """Класс для управления соединением с RabbitMQ."""

    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection = None

    async def connect(self):
        """Создаёт и возвращает соединение с RabbitMQ."""
        if not self.connection or self.connection.is_closed:
            try:
                self.connection = await aio_pika.connect_robust(
                    self.connection_url, timeout=10
                )
                logger.info("RPC: Подключение к RabbitMQ успешно установлено.")
            except Exception as e:
                logger.error("RPC: Ошибка подключения к RabbitMQ: %s", e)
                raise
        return self.connection

    async def reconnect(self):
        """Принудительно пересоздаёт соединение с RabbitMQ."""
        logger.warning("RPC: Принудительное переподключение к RabbitMQ...")
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
            except Exception:
                pass
        self.connection = None
        return await self.connect()

    async def close(self):
        """Закрывает соединение, если оно открыто."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RPC: Соединение с RabbitMQ закрыто.")

    async def __aenter__(self):
        """Контекстный менеджер для автоматического открытия соединения."""
        return await self.connect()

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Закрывает соединение при выходе из контекста."""
        await self.close()
