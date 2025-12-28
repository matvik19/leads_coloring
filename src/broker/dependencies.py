"""
Dependency Injection для FastStream handlers.
"""

import uuid
from typing import AsyncGenerator
from aiohttp import ClientSession, TCPConnector

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database import get_async_session
from src.common.log_config import subdomain_var, request_id_var
from src.amocrm.rate_limited_session import RateLimitedClientSession


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with get_async_session() as session:
        yield session


async def get_http_session() -> AsyncGenerator[RateLimitedClientSession, None]:
    """
    Dependency для получения HTTP клиент сессии с автоматическим rate limiting.

    Yields:
        RateLimitedClientSession: HTTP сессия с встроенным rate limiting для AmoCRM API.
    """
    async with ClientSession(connector=TCPConnector(ssl=False)) as session:
        # Оборачиваем обычную сессию в rate-limited wrapper
        rate_limited_session = RateLimitedClientSession(session)
        yield rate_limited_session


def setup_logging_context(subdomain: str | None = None) -> str:
    """
    Устанавливает контекст логирования (subdomain и request_id).

    Args:
        subdomain: Субдомен для логирования.

    Returns:
        str: ID запроса для трекинга.
    """
    # Генерируем request_id
    request_id = str(uuid.uuid4())[:12]
    request_id_var.set(request_id)

    # Устанавливаем subdomain если есть
    if subdomain:
        subdomain_var.set(subdomain)

    return request_id


def reset_logging_context():
    """
    Сбрасывает контекст логирования.
    """
    try:
        subdomain_var.set("unknown")
        request_id_var.set("")
    except LookupError:
        pass
