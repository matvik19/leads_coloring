"""
Middleware для логирования сообщений.
"""

import json
import uuid
from types import TracebackType

from faststream import BaseMiddleware

from app.core.logging import logger, subdomain_var, request_id_var


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для установки контекста логирования.

    Устанавливает subdomain и request_id из сообщения в contextvars,
    логирует начало и конец обработки.
    """

    async def on_receive(self) -> None:
        """
        Вызывается при получении сообщения из RabbitMQ.
        Устанавливает контекст логирования (subdomain, request_id).
        """
        try:
            # Получаем body как bytes и декодируем вручную
            body_bytes = getattr(self.msg, "body", b"")

            # Декодируем JSON из bytes
            if isinstance(body_bytes, bytes):
                body_str = body_bytes.decode("utf-8")
                body = json.loads(body_str)
            elif isinstance(body_bytes, str):
                body = json.loads(body_bytes)
            else:
                body = body_bytes  # Уже dict

            # Извлекаем subdomain из разных возможных ключей
            subdomain = body.get("subdomain") or body.get("account[subdomain]") or "unknown"

            # Генерируем request_id
            request_id = str(uuid.uuid4())[:12]

            # Устанавливаем contextvars
            self._subdomain_token = subdomain_var.set(subdomain)
            self._request_id_token = request_id_var.set(request_id)

            # Получаем имя очереди из routing_key
            queue_name = "unknown"
            routing_key = getattr(self.msg, "routing_key", None)
            consumer_tag = getattr(self.msg, "consumer_tag", None)

            if routing_key:
                queue_name = routing_key
            elif consumer_tag:
                queue_name = consumer_tag

            logger.info("Получено сообщение из очереди [%s]", queue_name)

        except Exception as e:
            logger.error("Ошибка в LoggingMiddleware.on_receive: %s", e, exc_info=True)
            # Устанавливаем дефолтные значения
            self._subdomain_token = subdomain_var.set("unknown")
            self._request_id_token = request_id_var.set(str(uuid.uuid4())[:12])

    async def after_processed(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> bool | None:
        """
        Вызывается после обработки сообщения.
        Логирует результат и сбрасывает контекст.
        """
        try:
            if exc_type is None:
                logger.info("Сообщение успешно обработано")
            else:
                logger.error(
                    "Ошибка при обработке сообщения: %s: %s",
                    exc_type.__name__,
                    exc_val,
                )
        finally:
            # Сбрасываем contextvars
            if hasattr(self, "_subdomain_token"):
                subdomain_var.reset(self._subdomain_token)
            if hasattr(self, "_request_id_token"):
                request_id_var.reset(self._request_id_token)

        return await super().after_processed(exc_type, exc_val, exc_tb)
