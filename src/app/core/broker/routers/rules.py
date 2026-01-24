"""
FastStream роутер для операций с правилами окраски.
"""

from typing import Annotated, Dict, Any

from faststream.rabbit import RabbitRouter, RabbitQueue
from faststream import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.broker.config import QueueNames
from app.core.broker.dependencies import get_db_session
from app.core.logging import logger
from app.schemas.coloring import (
    CreateRuleRequest,
    UpdateRuleRequest,
    RuleResponse,
)
from app.services.coloring_service import (
    create_rule,
    update_rule,
    get_rules_by_subdomain,
    delete_rule,
    update_priorities,
)
from app.services.condition_evaluator import evaluate_conditions


rules_router = RabbitRouter()


@rules_router.subscriber(
    RabbitQueue(QueueNames.RULES_CREATE, durable=True)
)
async def handle_create_rule(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Создание нового правила окраски.

    Args:
        data: Данные из RabbitMQ сообщения
        db_session: Сессия базы данных (DI)

    Returns:
        Dict с id созданного правила и статусом
    """
    try:
        # Валидация через Pydantic
        request = CreateRuleRequest(**data)

        # Создание правила
        rule = await create_rule(request, db_session)

        logger.info("Создано правило id=%s для subdomain=%s", rule.id, request.subdomain)

        return {
            "id": rule.id,
            "success": True
        }

    except Exception as e:
        logger.error("Ошибка при создании правила: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@rules_router.subscriber(
    RabbitQueue(QueueNames.RULES_UPDATE, durable=True)
)
async def handle_update_rule(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Обновление существующего правила.

    Args:
        data: Данные из RabbitMQ сообщения (должен содержать rule_id)
        db_session: Сессия базы данных (DI)

    Returns:
        Dict с id обновленного правила и статусом
    """
    try:
        rule_id = data.pop("rule_id")

        # Валидация через Pydantic
        request = UpdateRuleRequest(**data)

        # Обновление правила
        rule = await update_rule(rule_id, request, db_session)

        if not rule:
            logger.warning("Правило id=%s не найдено", rule_id)
            return {
                "success": False,
                "error": "Rule not found"
            }

        logger.info("Обновлено правило id=%s для subdomain=%s", rule.id, request.subdomain)

        return {
            "id": rule.id,
            "success": True
        }

    except Exception as e:
        logger.error("Ошибка при обновлении правила: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@rules_router.subscriber(
    RabbitQueue(QueueNames.RULES_LIST, durable=True)
)
async def handle_get_rules(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Получение списка всех правил для субдомена.

    Args:
        data: Данные из RabbitMQ сообщения (должен содержать subdomain)
        db_session: Сессия базы данных (DI)

    Returns:
        Dict со списком правил
    """
    try:
        subdomain = data.get("subdomain")

        if not subdomain:
            return {
                "success": False,
                "error": "subdomain is required"
            }

        # Получение правил
        rules = await get_rules_by_subdomain(subdomain, db_session)

        logger.info("Получено %s правил для subdomain=%s", len(rules), subdomain)

        return {
            "success": True,
            "rules": [RuleResponse.model_validate(rule).model_dump() for rule in rules]
        }

    except Exception as e:
        logger.error("Ошибка при получении списка правил: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@rules_router.subscriber(
    RabbitQueue(QueueNames.RULES_DELETE, durable=True)
)
async def handle_delete_rule(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Удаление правила.

    Args:
        data: Данные из RabbitMQ сообщения (должен содержать rule_id и subdomain)
        db_session: Сессия базы данных (DI)

    Returns:
        Dict со статусом удаления
    """
    try:
        rule_id = data.get("rule_id")
        subdomain = data.get("subdomain")

        if not rule_id or not subdomain:
            return {
                "success": False,
                "error": "rule_id and subdomain are required"
            }

        # Удаление правила
        deleted = await delete_rule(rule_id, subdomain, db_session)

        if not deleted:
            logger.warning("Правило id=%s не найдено для subdomain=%s", rule_id, subdomain)
            return {
                "success": False,
                "error": "Rule not found"
            }

        logger.info("Удалено правило id=%s для subdomain=%s", rule_id, subdomain)

        return {"success": True}

    except Exception as e:
        logger.error("Ошибка при удалении правила: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@rules_router.subscriber(
    RabbitQueue(QueueNames.PRIORITIES_UPDATE, durable=True)
)
async def handle_update_priorities(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Dict[str, Any]:
    """
    Обновление приоритетов правил.

    Args:
        data: Данные из RabbitMQ сообщения (subdomain, priorities)
        db_session: Сессия базы данных (DI)

    Returns:
        Dict со статусом обновления
    """
    try:
        subdomain = data.get("subdomain")
        priorities = data.get("priorities", [])

        if not subdomain or not priorities:
            return {
                "success": False,
                "error": "subdomain and priorities are required"
            }

        # Обновление приоритетов
        await update_priorities(subdomain, priorities, db_session)

        logger.info("Обновлены приоритеты для %s правил, subdomain=%s", len(priorities), subdomain)

        return {"success": True}

    except Exception as e:
        logger.error("Ошибка при обновлении приоритетов: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@rules_router.subscriber(
    RabbitQueue(QueueNames.RULES_TEST, durable=True)
)
async def handle_test_rule(
    data: dict,
) -> Dict[str, Any]:
    """
    Тестирование правила на конкретных данных лида.

    Args:
        data: Данные из RabbitMQ сообщения (conditions, lead_data)

    Returns:
        Dict с результатом тестирования
    """
    try:
        conditions = data.get("conditions")
        lead_data = data.get("lead_data")

        if not conditions or not lead_data:
            return {
                "success": False,
                "error": "conditions and lead_data are required"
            }

        # Тестирование условий
        matches = evaluate_conditions(conditions, lead_data)
        details = "Условие выполнено" if matches else "Условие не выполнено"

        logger.info("Тест правила: %s", details)

        return {
            "success": True,
            "matches": matches,
            "details": details
        }

    except Exception as e:
        logger.error("Ошибка при тестировании правила: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
