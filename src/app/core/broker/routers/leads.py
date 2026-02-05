"""
FastStream роутер для операций с лидами.
"""

from typing import Annotated, Dict, Any

from faststream.rabbit import RabbitRouter, RabbitQueue
from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broker.config import QueueNames
from app.core.broker.dependencies import get_db_session, get_http_session
from app.core.logging import logger
from app.schemas.coloring import GetStylesRequest, LeadStyle
from app.services.coloring_service import get_active_rules_by_subdomain
from app.services.condition_evaluator import evaluate_conditions
from app.amocrm.requests_amocrm import get_leads_by_ids
from app.amocrm.rate_limited_session import RateLimitedClientSession
from app.utils.tokens import get_tokens_from_service, get_headers


leads_router = RabbitRouter()


@leads_router.subscriber(
    RabbitQueue(QueueNames.LEADS_STYLES, durable=True)
)
async def handle_get_leads_styles(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    http_session: Annotated[RateLimitedClientSession, Depends(get_http_session)],
) -> Dict[str, Any]:
    """
    Получение стилей для лидов на основе правил.
    """
    try:
        # Валидация через Pydantic
        request = GetStylesRequest(**data)

        logger.info(
            "Запрос стилей для %s лидов, subdomain=%s",
            len(request.lead_ids),
            request.subdomain
        )

        # Получаем активные правила для субдомена
        rules = await get_active_rules_by_subdomain(request.subdomain, db_session)

        if not rules:
            logger.info("Нет активных правил для subdomain=%s", request.subdomain)
            return {
                "success": True,
                "styles": {}
            }

        # Получаем токены из сервиса токенов через RPC
        tokens = await get_tokens_from_service(request.subdomain)

        # Формируем headers с токеном доступа
        headers = await get_headers(request.subdomain, tokens["access_token"])

        try:
            leads_data = await get_leads_by_ids(
                request.lead_ids,
                request.subdomain,
                headers,
                http_session
            )
        except Exception as e:
            logger.error("Ошибка при получении лидов: %s", e, exc_info=True)
            return {"success": False, "styles": {}}

        # Применяем правила к каждому лиду
        styles = {}

        for lead_id in request.lead_ids:
            lead_data = leads_data.get(lead_id)

            if not lead_data:
                logger.debug("Лид %s не найден в AmoCRM", lead_id)
                continue

            # Проверяем правила по приоритету (от высшего к низшему)
            for rule in rules:
                try:
                    if evaluate_conditions(rule.conditions, lead_data):
                        # Лид подходит под правило - применяем стиль
                        styles[str(lead_id)] = {
                            "text_color": rule.style["text_color"],
                            "background_color": rule.style["background_color"],
                            "matched_rule_id": rule.id,
                            "matched_rule_name": rule.name
                        }
                        logger.debug("Лид %s подходит под правило %s", lead_id, rule.id)
                        break  # Применяем только первое подходящее правило
                except Exception as e:
                    logger.error(
                        "Ошибка при проверке правила %s для лида %s: %s",
                        rule.id,
                        lead_id,
                        e
                    )
                    continue

        logger.info(
            "Применены стили для %s лидов из %s",
            len(styles),
            len(request.lead_ids)
        )

        return {
            "success": True,
            "styles": styles
        }

    except Exception as e:
        logger.error("Ошибка при получении стилей: %s", e, exc_info=True)
        return {"success": False, "styles": {}}
