import ssl
from typing import AsyncGenerator, Dict, Any, List

from aiohttp import ClientSession, TCPConnector
from fastapi import HTTPException

import aiohttp

from app.core.logging import logger


async def get_client_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Асинхронная сессия для запросов к AmoCRM (с отключенной проверкой SSL)"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        yield session


async def get_lead_by_id(
    lead_id: int, subdomain: str, headers: dict, client_session: ClientSession
) -> Dict[str, Any]:
    """Получение объекта лида по id"""
    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/{lead_id}"

    try:
        async with client_session.get(url, headers=headers) as response:
            if response.status == 200:
                try:
                    data = await response.json()
                    return data
                except Exception as json_err:
                    logger.error("Ошибка парсинга JSON из ответа: %s", json_err)
                    raise HTTPException(status_code=500, detail="Failed to parse server response")
            elif response.status == 404:
                logger.warning("Лид с id %s не найден", lead_id)
                raise HTTPException(status_code=404, detail=f"Lead with id {lead_id} not found")
            else:
                error_message = await response.text()
                logger.error(
                    "Ошибка получения лида (статус %s): %s",
                    response.status,
                    error_message,
                )
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to fetch lead with id {lead_id}. Error: {error_message}",
                )

    except aiohttp.ClientError as client_err:
        logger.error("Сетевая ошибка при получении лида с id %s: %s", lead_id, client_err)
        raise HTTPException(status_code=502, detail="Bad Gateway - Error connecting to AmoCRM")

    except Exception as e:
        logger.error("Неожиданная ошибка при получении лида с id %s: %s", lead_id, e)
        raise HTTPException(
            status_code=500, detail=f"Unexpected error while fetching lead with id {lead_id}"
        )


async def get_leads_by_ids(
    lead_ids: List[int], subdomain: str, headers: dict, client_session: ClientSession
) -> Dict[int, Dict[str, Any]]:
    """
    Получение нескольких лидов по их ID.

    Args:
        lead_ids: Список ID лидов
        subdomain: Поддомен AmoCRM
        headers: Заголовки для авторизации
        client_session: HTTP сессия

    Returns:
        Словарь {lead_id: lead_data}
    """
    if not lead_ids:
        return {}

    # AmoCRM позволяет получить до 250 лидов за раз через фильтр по ID
    url = f"https://{subdomain}.amocrm.ru/api/v4/leads"

    # Формируем параметры запроса с фильтром по ID
    params = {}
    for idx, lead_id in enumerate(lead_ids[:250]):  # Ограничиваем 250 лидами
        params[f"filter[id][{idx}]"] = lead_id

    try:
        async with client_session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                try:
                    data = await response.json()
                    leads = data.get("_embedded", {}).get("leads", [])

                    # Преобразуем список лидов в словарь {id: lead_data}
                    result = {lead["id"]: lead for lead in leads}

                    logger.info("Получено %s лидов из %s запрошенных", len(result), len(lead_ids))
                    return result

                except Exception as json_err:
                    logger.error("Ошибка парсинга JSON из ответа: %s", json_err)
                    raise HTTPException(status_code=500, detail="Failed to parse server response")
            elif response.status == 204:
                logger.info("Лиды не найдены (статус 204)")
                return {}
            else:
                error_message = await response.text()
                logger.error(
                    "Ошибка получения лидов (статус %s): %s",
                    response.status,
                    error_message,
                )
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to fetch leads. Error: {error_message}",
                )

    except aiohttp.ClientError as client_err:
        logger.error("Сетевая ошибка при получении лидов: %s", client_err)
        raise HTTPException(status_code=502, detail="Bad Gateway - Error connecting to AmoCRM")

    except Exception as e:
        logger.error("Неожиданная ошибка при получении лидов: %s", e)
        raise HTTPException(
            status_code=500, detail="Unexpected error while fetching leads"
        )


async def get_custom_fields_for_leads(
    subdomain: str, headers: dict, client_session: ClientSession
) -> List[Dict[str, Any]]:
    """
    Получение списка кастомных полей для лидов.

    Returns:
        Список полей с их метаданными
    """
    url = f"https://{subdomain}.amocrm.ru/api/v4/leads/custom_fields"

    try:
        async with client_session.get(url, headers=headers) as response:
            if response.status == 200:
                try:
                    data = await response.json()
                    fields = data.get("_embedded", {}).get("custom_fields", [])
                    logger.info("Получено %s кастомных полей для лидов", len(fields))
                    return fields
                except Exception as json_err:
                    logger.error("Ошибка парсинга JSON: %s", json_err)
                    raise HTTPException(status_code=500, detail="Failed to parse server response")
            else:
                error_message = await response.text()
                logger.error("Ошибка получения полей (статус %s): %s", response.status, error_message)
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to fetch custom fields. Error: {error_message}",
                )
    except aiohttp.ClientError as client_err:
        logger.error("Сетевая ошибка при получении полей: %s", client_err)
        raise HTTPException(status_code=502, detail="Bad Gateway - Error connecting to AmoCRM")
    except Exception as e:
        logger.error("Неожиданная ошибка при получении полей: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
