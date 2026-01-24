"""
Утилиты для работы с токенами AmoCRM через сервис токенов с кешированием.
"""

import time
from typing import Dict, Optional

from app.core.broker.rpc import send_rpc_request_and_wait_for_reply
from app.core.settings import config
from app.core.logging import logger


# Локальный кеш токенов {subdomain: {tokens, expires_at}}
_tokens_cache: Dict[str, Dict] = {}

# TTL для кеша токенов в секундах (например, 50 минут, токены живут 1 час)
TOKEN_CACHE_TTL = 50 * 60


async def get_tokens_from_service(subdomain: str, force_refresh: bool = False) -> Dict[str, str]:
    """
    Получение токенов AmoCRM для указанного субдомена через RPC с кешированием.

    Использует локальный кеш для минимизации RPC запросов к сервису токенов.
    Токены кешируются на 50 минут (при TTL токена 60 минут).

    Args:
        subdomain: Субдомен AmoCRM (например, "example" для example.amocrm.ru)
        force_refresh: Принудительно обновить токены, игнорируя кеш

    Returns:
        Dict с ключами:
            - access_token: Токен доступа к AmoCRM API
            - refresh_token: Токен для обновления access_token

    Raises:
        ValueError: Если полученные токены невалидны (пустые)
        Exception: При ошибке получения токенов от сервиса

    Example:
        >>> tokens = await get_tokens_from_service("example")
        >>> access_token = tokens["access_token"]
        >>> refresh_token = tokens["refresh_token"]
    """
    # Проверяем кеш, если не требуется принудительное обновление
    if not force_refresh and subdomain in _tokens_cache:
        cached = _tokens_cache[subdomain]
        current_time = time.time()

        # Если токены еще валидны
        if current_time < cached["expires_at"]:
            logger.debug(
                "Используем кешированные токены для subdomain=%s (TTL: %s сек)",
                subdomain,
                int(cached["expires_at"] - current_time)
            )
            return {
                "access_token": cached["access_token"],
                "refresh_token": cached["refresh_token"],
            }
        else:
            logger.debug(
                "Кешированные токены для subdomain=%s истекли, обновляем",
                subdomain
            )

    # Получаем токены из сервиса через RPC
    try:
        logger.info("Запрашиваем токены в сервисе токенов для subdomain=%s", subdomain)

        # Получаем CLIENT_ID из конфигурации
        client_id = config.amocrm_cfg.CLIENT_ID

        if not client_id:
            logger.error("CLIENT_ID не настроен в конфигурации")
            raise ValueError("AmoCRM CLIENT_ID is not configured")

        # Отправляем RPC запрос в сервис токенов
        # Семафор внутри send_rpc_request_and_wait_for_reply обеспечивает
        # последовательное выполнение RPC запросов
        tokens = await send_rpc_request_and_wait_for_reply(
            subdomain=subdomain,
            client_id=client_id,
        )

        # Валидация полученных токенов
        if not tokens.get("access_token") or not tokens.get("refresh_token"):
            logger.error("Получены невалидные токены для subdomain=%s", subdomain)
            raise ValueError("Invalid tokens received from token service")

        # Сохраняем в кеш
        _tokens_cache[subdomain] = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_at": time.time() + TOKEN_CACHE_TTL,
        }

        logger.info(
            "Токены успешно получены и закешированы для subdomain=%s (TTL: %s мин)",
            subdomain,
            TOKEN_CACHE_TTL // 60
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }

    except Exception as e:
        logger.error(
            "Ошибка при получении токенов для subdomain=%s: %s",
            subdomain,
            e,
            exc_info=True
        )
        raise


def clear_token_cache(subdomain: Optional[str] = None):
    """
    Очистка кеша токенов.

    Args:
        subdomain: Субдомен для очистки. Если None - очищается весь кеш.

    Example:
        >>> clear_token_cache("example")  # Очистить для одного субдомена
        >>> clear_token_cache()  # Очистить весь кеш
    """
    if subdomain:
        if subdomain in _tokens_cache:
            del _tokens_cache[subdomain]
            logger.info("Кеш токенов очищен для subdomain=%s", subdomain)
    else:
        _tokens_cache.clear()
        logger.info("Кеш токенов полностью очищен")


async def get_headers(subdomain: str, access_token: str) -> Dict[str, str]:
    """
    Формирование HTTP заголовков для запросов к AmoCRM API.

    Args:
        subdomain: Субдомен AmoCRM
        access_token: Токен доступа к AmoCRM API

    Returns:
        Dict с заголовками для HTTP запросов к AmoCRM API

    Example:
        >>> tokens = await get_tokens_from_service("example")
        >>> headers = await get_headers("example", tokens["access_token"])
        >>> # Использование headers для API запросов
    """
    headers = {
        "Host": f"{subdomain}.amocrm.ru",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    return headers
