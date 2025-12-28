"""REST API роутеры для управления правилами окраски"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import ClientSession

from src.common.database import get_async_session_router
from src.common.log_config import logger
from src.amocrm.requests_amocrm import get_client_session, get_custom_fields_for_leads, get_leads_by_ids
from src.rules.schemas import (
    CreateRuleRequest,
    CreateRuleResponse,
    UpdateRuleRequest,
    RuleResponse,
    RulesListResponse,
    DeleteRuleResponse,
    UpdatePrioritiesRequest,
    UpdatePrioritiesResponse,
    GetStylesRequest,
    GetStylesResponse,
    TestRuleRequest,
    TestRuleResponse,
    GetDealFieldsResponse,
    DealField,
    LeadStyle,
)
from src.rules.services import (
    create_rule,
    update_rule,
    get_rules_by_subdomain,
    delete_rule,
    update_priorities,
    get_active_rules_by_subdomain,
)
from src.conditions.evaluator import evaluate_conditions

router = APIRouter(prefix="/api", tags=["Rules"])


@router.get("/deal-fields", response_model=GetDealFieldsResponse)
async def get_deal_fields(
    subdomain: str = Query(..., description="Субдомен AmoCRM"),
    access_token: str = Query(..., description="Токен доступа AmoCRM"),
    client_session: ClientSession = Depends(get_client_session)
):
    """
    Получение списка полей сделок из AmoCRM.

    Возвращает стандартные и кастомные поля для использования в правилах.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    # Стандартные поля лидов
    standard_fields = [
        DealField(id="name", name="Название", type="string"),
        DealField(id="price", name="Бюджет", type="number"),
        DealField(id="status_id", name="Статус", type="enum"),
        DealField(id="pipeline_id", name="Воронка", type="enum"),
        DealField(id="responsible_user_id", name="Ответственный", type="enum"),
        DealField(id="created_at", name="Дата создания", type="date"),
        DealField(id="updated_at", name="Дата изменения", type="date"),
        DealField(id="closed_at", name="Дата закрытия", type="date"),
    ]

    # Получаем кастомные поля
    try:
        custom_fields_data = await get_custom_fields_for_leads(subdomain, headers, client_session)

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

            custom_fields.append(
                DealField(
                    id=str(field.get("id")),
                    name=field.get("name", ""),
                    type=field_type
                )
            )

        all_fields = standard_fields + custom_fields
        logger.info("Получено %s полей для subdomain=%s", len(all_fields), subdomain)

        return GetDealFieldsResponse(fields=all_fields)

    except Exception as e:
        logger.error("Ошибка при получении полей: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch fields: {str(e)}")


@router.post("/rules", response_model=CreateRuleResponse)
async def create_new_rule(
    request: CreateRuleRequest,
    session: AsyncSession = Depends(get_async_session_router)
):
    """
    Создание нового правила окраски.
    """
    rule = await create_rule(request, session)
    return CreateRuleResponse(id=rule.id, success=True)


@router.put("/rules/{rule_id}", response_model=CreateRuleResponse)
async def update_existing_rule(
    rule_id: int,
    request: UpdateRuleRequest,
    session: AsyncSession = Depends(get_async_session_router)
):
    """
    Обновление существующего правила.
    """
    rule = await update_rule(rule_id, request, session)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return CreateRuleResponse(id=rule.id, success=True)


@router.get("/rules", response_model=RulesListResponse)
async def get_rules(
    subdomain: str = Query(..., description="Субдомен AmoCRM"),
    session: AsyncSession = Depends(get_async_session_router)
):
    """
    Получение списка всех правил для субдомена.
    """
    rules = await get_rules_by_subdomain(subdomain, session)

    return RulesListResponse(
        rules=[RuleResponse.model_validate(rule) for rule in rules]
    )


@router.delete("/rules/{rule_id}", response_model=DeleteRuleResponse)
async def delete_existing_rule(
    rule_id: int,
    subdomain: str = Query(..., description="Субдомен AmoCRM"),
    session: AsyncSession = Depends(get_async_session_router)
):
    """
    Удаление правила.
    """
    deleted = await delete_rule(rule_id, subdomain, session)

    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")

    return DeleteRuleResponse(success=True)


@router.put("/rules/priorities", response_model=UpdatePrioritiesResponse)
async def update_rule_priorities(
    request: UpdatePrioritiesRequest,
    session: AsyncSession = Depends(get_async_session_router)
):
    """
    Обновление приоритетов правил.
    """
    await update_priorities(request.subdomain, request.priorities, session)
    return UpdatePrioritiesResponse(success=True)


@router.post("/leads/styles", response_model=GetStylesResponse)
async def get_leads_styles(
    request: GetStylesRequest,
    session: AsyncSession = Depends(get_async_session_router),
    client_session: ClientSession = Depends(get_client_session)
):
    """
    Получение стилей для лидов на основе правил.

    Возвращает только те лиды, которые подходят под правила.
    """
    logger.info("Запрос стилей для %s лидов, subdomain=%s", len(request.lead_ids), request.subdomain)

    # Получаем активные правила для субдомена
    rules = await get_active_rules_by_subdomain(request.subdomain, session)

    if not rules:
        logger.info("Нет активных правил для subdomain=%s", request.subdomain)
        return GetStylesResponse(styles={})

    # Получаем данные лидов из AmoCRM
    headers = {"Authorization": f"Bearer {request.access_token}"}

    try:
        leads_data = await get_leads_by_ids(request.lead_ids, request.subdomain, headers, client_session)
    except Exception as e:
        logger.error("Ошибка при получении лидов: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")

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
                    styles[str(lead_id)] = LeadStyle(
                        text_color=rule.style["text_color"],
                        background_color=rule.style["background_color"],
                        matched_rule_id=rule.id,
                        matched_rule_name=rule.name
                    )
                    logger.debug("Лид %s подходит под правило %s", lead_id, rule.id)
                    break  # Применяем только первое подходящее правило
            except Exception as e:
                logger.error("Ошибка при проверке правила %s для лида %s: %s", rule.id, lead_id, e)
                continue

    logger.info("Применены стили для %s лидов из %s", len(styles), len(request.lead_ids))
    return GetStylesResponse(styles=styles)


@router.post("/rules/test", response_model=TestRuleResponse)
async def test_rule(request: TestRuleRequest):
    """
    Тестирование правила на конкретных данных лида.

    Используется для отладки и проверки условий.
    """
    try:
        conditions_dict = request.conditions.model_dump()
        matches = evaluate_conditions(conditions_dict, request.lead_data)

        details = "Условие выполнено" if matches else "Условие не выполнено"

        logger.info("Тест правила: %s", details)
        return TestRuleResponse(matches=matches, details=details)

    except Exception as e:
        logger.error("Ошибка при тестировании правила: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to test rule: {str(e)}")
