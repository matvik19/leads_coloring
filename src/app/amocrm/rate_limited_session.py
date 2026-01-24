"""
Обертка для aiohttp.ClientSession с автоматическим rate limiting.
"""

from typing import Any, Optional
from aiohttp import ClientSession, ClientResponse
from app.amocrm.rate_limiter import amocrm_rate_limiter


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

    async def get(self, url: str, **kwargs) -> ClientResponse:
        """GET запрос с rate limiting."""
        await amocrm_rate_limiter.acquire()
        return await self._session.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> ClientResponse:
        """POST запрос с rate limiting."""
        await amocrm_rate_limiter.acquire()
        return await self._session.post(url, **kwargs)

    async def patch(self, url: str, **kwargs) -> ClientResponse:
        """PATCH запрос с rate limiting."""
        await amocrm_rate_limiter.acquire()
        return await self._session.patch(url, **kwargs)

    async def put(self, url: str, **kwargs) -> ClientResponse:
        """PUT запрос с rate limiting."""
        await amocrm_rate_limiter.acquire()
        return await self._session.put(url, **kwargs)

    async def delete(self, url: str, **kwargs) -> ClientResponse:
        """DELETE запрос с rate limiting."""
        await amocrm_rate_limiter.acquire()
        return await self._session.delete(url, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Проксируем все остальные атрибуты к оригинальной сессии."""
        return getattr(self._session, name)
