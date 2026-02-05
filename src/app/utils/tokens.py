import time
from typing import Dict, Optional

from app.core.broker.rpc import send_rpc_request_and_wait_for_reply
from app.core.settings import config
from app.core.logging import logger


async def get_tokens_from_service(subdomain: str, force_refresh: bool = False) -> Dict[str, str]:
    """
    Получение токенов AmoCRM для указанного субдомена через RPC
    """

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

        logger.info(
            "Токены успешно получены для subdomain=%s", subdomain,
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


async def get_headers(subdomain: str, access_token: str) -> Dict[str, str]:
    """
    Формирование HTTP заголовков для запросов к AmoCRM API.
    """
    headers = {
        "Host": f"{subdomain}.amocrm.ru",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    return headers
