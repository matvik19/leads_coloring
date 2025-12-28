"""
Middleware для автоматических retry попыток при ошибках.
"""

import asyncio
from types import TracebackType

from faststream import BaseMiddleware

from app.core.logging import logger
from app.core.settings import config
# Config constants
MAX_RETRY_COUNT = 3
RETRY_DELAY = 5  # MAX_RETRY_COUNT, RETRY_DELAY


class RetryMiddleware(BaseMiddleware):
    """
    Middleware для автоматических retry попыток при ошибках обработки сообщений.
    """

    async def on_receive(self) -> None:
        """Вызывается при получении сообщения."""
        # Инициализируем счетчик попыток
        self._attempt = 0
        self._max_retries = MAX_RETRY_COUNT

    async def after_processed(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> bool | None:
        """
        Вызывается после обработки сообщения.

        Если произошла ошибка и не исчерпаны попытки - повторяет обработку.
        """
        if exc_type is not None:
            self._attempt += 1

            if self._attempt < self._max_retries:
                logger.warning(
                    "Ошибка обработки сообщения (попытка %s/%s): %s. Повтор через %s сек",
                    self._attempt,
                    self._max_retries,
                    exc_val,
                    RETRY_DELAY
                )

                # Ждем перед повторной попыткой
                await asyncio.sleep(RETRY_DELAY)

                # Возвращаем False чтобы сообщение не было подтверждено
                # и обработано повторно
                return False
            else:
                logger.error(
                    "Исчерпаны все попытки обработки сообщения (%s/%s): %s",
                    self._attempt,
                    self._max_retries,
                    exc_val
                )

        return await super().after_processed(exc_type, exc_val, exc_tb)
