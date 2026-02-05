"""
Rate Limiter для AmoCRM API.

Ограничивает количество запросов до 7 в секунду (лимит AmoCRM).
Использует Token Bucket алгоритм для плавного распределения запросов.
"""

import asyncio
import time
from typing import Optional
from contextlib import asynccontextmanager

from app.core.logging import logger


class AmoCRMRateLimiter:
    """
    Rate Limiter для AmoCRM API используя Token Bucket алгоритм.

    AmoCRM допускает максимум 7 запросов в секунду.
    Используем консервативное значение 6 RPS для безопасности.
    """

    def __init__(self, rate: float = 6.0, burst: int = 6):
        """
        Args:
            rate: Максимальное количество запросов в секунду (default: 6)
            burst: Максимальное количество токенов (burst capacity)
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Получить разрешение на выполнение запроса.
        Блокирует выполнение если нет доступных токенов.
        """
        async with self.lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_update

                # Добавляем новые токены на основе прошедшего времени
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_update = now

                if self.tokens >= 1.0:
                    # Есть токен - используем его
                    self.tokens -= 1.0
                    return

                # Нет токенов - ждем пока появится хотя бы один
                wait_time = (1.0 - self.tokens) / self.rate
                logger.debug("Rate limit: ожидание %.3f секунд", wait_time)
                await asyncio.sleep(wait_time)


# Глобальный экземпляр Rate Limiter для AmoCRM
amocrm_rate_limiter = AmoCRMRateLimiter(rate=6.0, burst=6)


@asynccontextmanager
async def rate_limited_request():
    """
    Context manager для rate-limited запросов к AmoCRM.

    Usage:
        async with rate_limited_request():
            response = await session.get(url)
    """
    await amocrm_rate_limiter.acquire()
    try:
        yield
    finally:
        pass


async def retry_on_429(
    func,
    *args,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    **kwargs
):
    """
    Retry функции при получении 429 ошибки с exponential backoff.

    Args:
        func: Async функция для выполнения
        max_retries: Максимальное количество повторных попыток
        initial_delay: Начальная задержка в секундах
        max_delay: Максимальная задержка в секундах
        backoff_factor: Множитель для exponential backoff

    Returns:
        Результат выполнения функции

    Raises:
        Exception: Если все попытки исчерпаны
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Проверяем, является ли это 429 ошибкой
            error_str = str(e)
            if "429" not in error_str and "Too Many Requests" not in error_str:
                # Не 429 ошибка - пробрасываем дальше
                raise

            if attempt == max_retries:
                logger.error(
                    "Исчерпаны все попытки (%s) для запроса. Последняя ошибка: %s",
                    max_retries,
                    e
                )
                raise

            # Логируем retry
            logger.warning(
                "Получена 429 ошибка. Retry попытка %s/%s через %.2f сек",
                attempt + 1,
                max_retries,
                delay
            )

            await asyncio.sleep(delay)

            # Увеличиваем задержку с exponential backoff
            delay = min(delay * backoff_factor, max_delay)

    # Это не должно выполниться, но на всякий случай
    if last_exception:
        raise last_exception
