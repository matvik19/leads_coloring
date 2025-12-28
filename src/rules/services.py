"""Сервисы для работы с правилами окраски"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.rules.models import ColoringRule
from src.rules.schemas import (
    CreateRuleRequest,
    UpdateRuleRequest,
    PriorityUpdate,
)
from src.common.log_config import logger


async def create_rule(
    request: CreateRuleRequest,
    session: AsyncSession
) -> ColoringRule:
    """
    Создает новое правило окраски.

    Args:
        request: Данные для создания правила
        session: Сессия БД

    Returns:
        Созданное правило
    """
    rule = ColoringRule(
        subdomain=request.subdomain,
        name=request.name,
        is_active=request.is_active,
        priority=request.priority,
        conditions=request.conditions.model_dump(),
        style=request.style.model_dump(),
    )

    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    logger.info("Создано новое правило ID=%s для subdomain=%s", rule.id, request.subdomain)
    return rule


async def update_rule(
    rule_id: int,
    request: UpdateRuleRequest,
    session: AsyncSession
) -> Optional[ColoringRule]:
    """
    Обновляет существующее правило.

    Args:
        rule_id: ID правила
        request: Данные для обновления
        session: Сессия БД

    Returns:
        Обновленное правило или None если не найдено
    """
    stmt = select(ColoringRule).where(
        ColoringRule.id == rule_id,
        ColoringRule.subdomain == request.subdomain
    )
    result = await session.execute(stmt)
    rule = result.scalar_one_or_none()

    if not rule:
        logger.warning("Правило ID=%s не найдено для subdomain=%s", rule_id, request.subdomain)
        return None

    # Обновляем только переданные поля
    if request.name is not None:
        rule.name = request.name
    if request.is_active is not None:
        rule.is_active = request.is_active
    if request.priority is not None:
        rule.priority = request.priority
    if request.conditions is not None:
        rule.conditions = request.conditions.model_dump()
    if request.style is not None:
        rule.style = request.style.model_dump()

    await session.commit()
    await session.refresh(rule)

    logger.info("Обновлено правило ID=%s для subdomain=%s", rule_id, request.subdomain)
    return rule


async def get_rules_by_subdomain(
    subdomain: str,
    session: AsyncSession
) -> List[ColoringRule]:
    """
    Получает все правила для субдомена.

    Args:
        subdomain: Субдомен AmoCRM
        session: Сессия БД

    Returns:
        Список правил, отсортированный по приоритету (от высшего к низшему)
    """
    stmt = select(ColoringRule).where(
        ColoringRule.subdomain == subdomain
    ).order_by(ColoringRule.priority.desc(), ColoringRule.id.asc())

    result = await session.execute(stmt)
    rules = result.scalars().all()

    logger.info("Получено %s правил для subdomain=%s", len(rules), subdomain)
    return list(rules)


async def get_active_rules_by_subdomain(
    subdomain: str,
    session: AsyncSession
) -> List[ColoringRule]:
    """
    Получает активные правила для субдомена.

    Args:
        subdomain: Субдомен AmoCRM
        session: Сессия БД

    Returns:
        Список активных правил, отсортированный по приоритету
    """
    stmt = select(ColoringRule).where(
        ColoringRule.subdomain == subdomain,
        ColoringRule.is_active == True
    ).order_by(ColoringRule.priority.desc(), ColoringRule.id.asc())

    result = await session.execute(stmt)
    rules = result.scalars().all()

    logger.info("Получено %s активных правил для subdomain=%s", len(rules), subdomain)
    return list(rules)


async def delete_rule(
    rule_id: int,
    subdomain: str,
    session: AsyncSession
) -> bool:
    """
    Удаляет правило.

    Args:
        rule_id: ID правила
        subdomain: Субдомен AmoCRM
        session: Сессия БД

    Returns:
        True если правило удалено, False если не найдено
    """
    stmt = delete(ColoringRule).where(
        ColoringRule.id == rule_id,
        ColoringRule.subdomain == subdomain
    )

    result = await session.execute(stmt)
    await session.commit()

    deleted = result.rowcount > 0

    if deleted:
        logger.info("Удалено правило ID=%s для subdomain=%s", rule_id, subdomain)
    else:
        logger.warning("Правило ID=%s не найдено для subdomain=%s", rule_id, subdomain)

    return deleted


async def update_priorities(
    subdomain: str,
    priorities: List[PriorityUpdate],
    session: AsyncSession
) -> bool:
    """
    Обновляет приоритеты правил.

    Args:
        subdomain: Субдомен AmoCRM
        priorities: Список обновлений приоритетов
        session: Сессия БД

    Returns:
        True если обновление прошло успешно
    """
    for priority_update in priorities:
        stmt = update(ColoringRule).where(
            ColoringRule.id == priority_update.id,
            ColoringRule.subdomain == subdomain
        ).values(priority=priority_update.priority)

        await session.execute(stmt)

    await session.commit()

    logger.info("Обновлены приоритеты %s правил для subdomain=%s", len(priorities), subdomain)
    return True


async def get_rule_by_id(
    rule_id: int,
    subdomain: str,
    session: AsyncSession
) -> Optional[ColoringRule]:
    """
    Получает правило по ID.

    Args:
        rule_id: ID правила
        subdomain: Субдомен AmoCRM
        session: Сессия БД

    Returns:
        Правило или None если не найдено
    """
    stmt = select(ColoringRule).where(
        ColoringRule.id == rule_id,
        ColoringRule.subdomain == subdomain
    )

    result = await session.execute(stmt)
    rule = result.scalar_one_or_none()

    return rule
