"""
Обертка для aiohttp.ClientSession с автоматическим rate limiting.
"""

from typing import Any
from aiohttp import ClientSession
from app.amocrm.rate_limiter import amocrm_rate_limiter


class RateLimitedContextManager:
    """
    Context manager для запросов с rate limiting.
    Позволяет использовать `async with session.get(...) as response`.
    """

    def __init__(self, coro):
        self._coro = coro
        self._response = None

    async def __aenter__(self):
        await amocrm_rate_limiter.acquire()
        self._response = await self._coro
        return self._response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._response is not None:
            self._response.release()
        return False


class RateLimitedClientSession:
    """
    Обертка для aiohttp.ClientSession с автоматическим rate limiting.

    Все HTTP методы автоматически соблюдают rate limit перед выполнением запроса.
    """

    def __init__(self, session: ClientSession):
        """
        Args:
            session: aiohttp.ClientSession для оборачивания
        """
        self._session = session

    def get(self, url: str, **kwargs) -> RateLimitedContextManager:
        """GET запрос с rate limiting."""
        return RateLimitedContextManager(self._session.get(url, **kwargs))

    def post(self, url: str, **kwargs) -> RateLimitedContextManager:
        """POST запрос с rate limiting."""
        return RateLimitedContextManager(self._session.post(url, **kwargs))

    def patch(self, url: str, **kwargs) -> RateLimitedContextManager:
        """PATCH запрос с rate limiting."""
        return RateLimitedContextManager(self._session.patch(url, **kwargs))

    def put(self, url: str, **kwargs) -> RateLimitedContextManager:
        """PUT запрос с rate limiting."""
        return RateLimitedContextManager(self._session.put(url, **kwargs))

    def delete(self, url: str, **kwargs) -> RateLimitedContextManager:
        """DELETE запрос с rate limiting."""
        return RateLimitedContextManager(self._session.delete(url, **kwargs))

    def __getattr__(self, name: str) -> Any:
        """Проксируем все остальные атрибуты к оригинальной сессии."""
        return getattr(self._session, name)
