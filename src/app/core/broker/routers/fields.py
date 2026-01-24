"""
FastStream роутер для операций с полями сделок AmoCRM.
"""

from typing import Annotated, Dict, Any

from faststream.rabbit import RabbitRouter, RabbitQueue
from faststream import Depends

from app.core.broker.config import QueueNames
from app.core.broker.dependencies import get_http_session
from app.core.logging import logger
from app.schemas.coloring import DealField
from app.amocrm.requests_amocrm import get_custom_fields_for_leads
from app.amocrm.rate_limited_session import RateLimitedClientSession
from app.utils.tokens import get_tokens_from_service, get_headers


fields_router = RabbitRouter()


@fields_router.subscriber(
    RabbitQueue(QueueNames.DEAL_FIELDS_GET, durable=True)
)
async def handle_get_deal_fields(
    data: dict,
    http_session: Annotated[RateLimitedClientSession, Depends(get_http_session)],
) -> Dict[str, Any]:
    """
    Получение списка полей сделок из AmoCRM.

    Args:
        data: Данные из RabbitMQ сообщения (subdomain)
        http_session: HTTP клиент с rate limiting (DI)

    Returns:
        Dict со списком полей (стандартные + кастомные)
    """
    try:
        subdomain = data.get("subdomain")

        if not subdomain:
            return {
                "success": False,
                "error": "subdomain is required"
            }

        # Получаем токены из сервиса токенов через RPC
        tokens = await get_tokens_from_service(subdomain)

        # Формируем headers с токеном доступа
        headers = await get_headers(subdomain, tokens["access_token"])

        # Стандартные поля лидов
        standard_fields = [
            {"id": "name", "name": "Название", "type": "string"},
            {"id": "price", "name": "Бюджет", "type": "number"},
            {"id": "status_id", "name": "Статус", "type": "enum"},
            {"id": "pipeline_id", "name": "Воронка", "type": "enum"},
            {"id": "responsible_user_id", "name": "Ответственный", "type": "enum"},
            {"id": "created_at", "name": "Дата создания", "type": "date"},
            {"id": "updated_at", "name": "Дата изменения", "type": "date"},
            {"id": "closed_at", "name": "Дата закрытия", "type": "date"},
        ]

        # Получаем кастомные поля
        try:
            custom_fields_data = await get_custom_fields_for_leads(
                subdomain,
                headers,
                http_session
            )

            custom_fields = []
            for field in custom_fields_data:
                field_type = "string"

                if field.get("type") == "numeric":
                    field_type = "number"
                elif field.get("type") == "date":
                    field_type = "date"
                elif field.get("type") in ["select", "multiselect", "radiobutton"]:
                    field_type = "enum"
                elif field.get("type") == "checkbox":
                    field_type = "boolean"

                custom_fields.append({
                    "id": str(field.get("id")),
                    "name": field.get("name", ""),
                    "type": field_type
                })

            all_fields = standard_fields + custom_fields

            logger.info("Получено %s полей для subdomain=%s", len(all_fields), subdomain)

            return {
                "success": True,
                "fields": all_fields
            }

        except Exception as e:
            logger.error("Ошибка при получении кастомных полей: %s", e, exc_info=True)
            return {
                "success": False,
                "error": f"Failed to fetch custom fields: {str(e)}"
            }

    except Exception as e:
        logger.error("Ошибка при получении полей сделок: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
