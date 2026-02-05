"""
Dependency Injection для FastStream handlers.
"""

import uuid
from typing import AsyncGenerator

from aiohttp import ClientSession, TCPConnector
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.async_session import get_session
from app.amocrm.rate_limited_session import RateLimitedClientSession
from app.core.logging import request_id_var, subdomain_var


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    DI для получения асинхронной сессии базы данных.

    Yields:
        AsyncSession: Сессия для работы с PostgreSQL
    """
    async for session in get_session():
        yield session


async def get_http_session() -> AsyncGenerator[RateLimitedClientSession, None]:
    """
    DI для получения HTTP сессии с rate limiting.

    Yields:
        RateLimitedClientSession: HTTP клиент с ограничением по rate для AmoCRM API
    """
    async with ClientSession(
        connector=TCPConnector(ssl=False, limit=100)
    ) as session:
        rate_limited_session = RateLimitedClientSession(session)
        yield rate_limited_session


def setup_logging_context(subdomain: str | None = None) -> str:
    """
    Установка контекста логирования через contextvars.

    Args:
        subdomain: Субдомен AmoCRM для контекста

    Returns:
        str: Сгенерированный request_id
    """
    request_id = str(uuid.uuid4())[:12]
    request_id_var.set(request_id)

    if subdomain:
        subdomain_var.set(subdomain)

    return request_id
