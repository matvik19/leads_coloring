"""
RPC клиент для взаимодействия с внешними сервисами через RabbitMQ.
"""

import asyncio
import json
from typing import Dict, Any

from app.core.logging import logger


# Семафор для предотвращения одновременных RPC вызовов
# Это необходимо для избежания ошибки "reply consumer already set"
_rpc_semaphore = asyncio.Semaphore(1)


async def send_rpc_request_and_wait_for_reply(
    subdomain: str,
    client_id: str,
    timeout: int = 30,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Отправка RPC запроса в сервис токенов и ожидание ответа.

    Args:
        subdomain: Субдомен AmoCRM для получения токенов
        client_id: ID клиента OAuth AmoCRM
        timeout: Таймаут ожидания ответа в секундах (по умолчанию 30)
        max_retries: Максимальное количество попыток (по умолчанию 3)

    Returns:
        Dict с access_token и refresh_token

    Raises:
        TimeoutError: Если не удалось получить ответ за указанное время
        Exception: При других ошибках
    """
    request_data = {
        "subdomain": subdomain,
        "client_id": client_id,
    }

    for attempt in range(max_retries):
        try:
            # Используем семафор для предотвращения конкурентных RPC вызовов
            async with _rpc_semaphore:
                logger.info(
                    "Отправляем RPC запрос в сервис токенов (попытка %s/%s)",
                    attempt + 1,
                    max_retries
                )

                # Импортируем broker внутри функции, чтобы избежать циклических импортов
                from app.core.broker.app import broker

                # FastStream автоматически обрабатывает correlation_id и reply_to
                response = await broker.request(
                    message=request_data,
                    queue="tokens_get_user",
                    timeout=timeout,
                )

                # Десериализация ответа
                tokens = json.loads(response.body)

                logger.info("Получен ответ от сервиса токенов для subdomain=%s", subdomain)
                return tokens

        except TimeoutError:
            if attempt < max_retries - 1:
                # Экспоненциальный backoff: 0.5s, 1s, 2s
                wait_time = 0.5 * (2 ** attempt)
                logger.warning(
                    "Таймаут при запросе токенов, повторная попытка через %ss",
                    wait_time
                )
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(
                    "Не удалось получить токены после %s попыток",
                    max_retries
                )
                raise

        except Exception as e:
            logger.error(
                "Ошибка при RPC запросе токенов (попытка %s/%s): %s",
                attempt + 1,
                max_retries,
                e,
                exc_info=True
            )
            if attempt < max_retries - 1:
                wait_time = 0.5 * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue
            else:
                raise

    # Этот код не должен быть достигнут
    raise Exception("Неожиданная ошибка в RPC клиенте")
