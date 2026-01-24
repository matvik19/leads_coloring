"""
Утилиты для работы с токенами AmoCRM через сервис токенов.
"""

from typing import Dict

from app.core.broker.rpc import send_rpc_request_and_wait_for_reply
from app.core.settings import config
from app.core.logging import logger


async def get_tokens_from_service(subdomain: str) -> Dict[str, str]:
    """
    Получение токенов AmoCRM для указанного субдомена через RPC.

    Отправляет асинхронный запрос в сервис токенов через RabbitMQ
    и ожидает получения access_token и refresh_token.

    Args:
        subdomain: Субдомен AmoCRM (например, "example" для example.amocrm.ru)

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
    try:
        logger.info("Запрашиваем токены в сервисе токенов для subdomain=%s", subdomain)

        # Получаем CLIENT_ID из конфигурации
        client_id = config.amocrm_cfg.CLIENT_ID

        if not client_id:
            logger.error("CLIENT_ID не настроен в конфигурации")
            raise ValueError("AmoCRM CLIENT_ID is not configured")

        # Отправляем RPC запрос в сервис токенов
        tokens = await send_rpc_request_and_wait_for_reply(
            subdomain=subdomain,
            client_id=client_id,
        )

        # Валидация полученных токенов
        if not tokens.get("access_token") or not tokens.get("refresh_token"):
            logger.error("Получены невалидные токены для subdomain=%s", subdomain)
            raise ValueError("Invalid tokens received from token service")

        logger.info("Токены успешно получены для subdomain=%s", subdomain)
        return tokens

    except Exception as e:
        logger.error(
            "Ошибка при получении токенов для subdomain=%s: %s",
            subdomain,
            e,
            exc_info=True
        )
        raise


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
