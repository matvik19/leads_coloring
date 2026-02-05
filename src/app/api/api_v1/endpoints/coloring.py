"""
REST API роутеры для тестирования RabbitMQ через HTTP (RPC прокси).

Все ручки отправляют сообщения в RabbitMQ и ждут ответа от worker'а.
Используются только для тестирования в Swagger UI.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query

from app.core.logging import logger
from app.core.broker.app import broker
from app.core.broker.config import QueueNames
from app.schemas.coloring import (
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
    LeadStyle,
)

router = APIRouter(prefix="/api", tags=["Coloring Rules (RPC Proxy)"])

# Таймаут для RPC запросов (секунды)
RPC_TIMEOUT = 30.0


@router.post("/rules", response_model=CreateRuleResponse)
async def create_new_rule(request: CreateRuleRequest):
    """
    Создание нового правила окраски.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    """
    logger.info("HTTP -> RabbitMQ RPC: создание правила для subdomain=%s", request.subdomain)

    response = await broker.publish(
        request.model_dump(),
        queue=QueueNames.RULES_CREATE,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))

    return CreateRuleResponse(id=response["id"], success=True)


@router.put("/rules/{rule_id}", response_model=CreateRuleResponse)
async def update_existing_rule(rule_id: int, request: UpdateRuleRequest):
    """
    Обновление существующего правила.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    """
    logger.info("HTTP -> RabbitMQ RPC: обновление правила id=%s", rule_id)

    # Добавляем rule_id в данные для worker'а
    data = request.model_dump()
    data["rule_id"] = rule_id

    response = await broker.publish(
        data,
        queue=QueueNames.RULES_UPDATE,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        error = response.get("error", "Unknown error")
        if error == "Rule not found":
            raise HTTPException(status_code=404, detail=error)
        raise HTTPException(status_code=400, detail=error)

    return CreateRuleResponse(id=response["id"], success=True)


@router.get("/rules", response_model=RulesListResponse)
async def get_rules(subdomain: str = Query(..., description="Субдомен AmoCRM")):
    """
    Получение списка всех правил для субдомена.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    """
    logger.info("HTTP -> RabbitMQ RPC: получение правил для subdomain=%s", subdomain)

    response = await broker.publish(
        {"subdomain": subdomain},
        queue=QueueNames.RULES_LIST,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))

    return RulesListResponse(
        rules=[RuleResponse.model_validate(rule) for rule in response["rules"]]
    )


@router.delete("/rules/{rule_id}", response_model=DeleteRuleResponse)
async def delete_existing_rule(
    rule_id: int,
    subdomain: str = Query(..., description="Субдомен AmoCRM"),
):
    """
    Удаление правила.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    """
    logger.info("HTTP -> RabbitMQ RPC: удаление правила id=%s, subdomain=%s", rule_id, subdomain)

    response = await broker.publish(
        {"rule_id": rule_id, "subdomain": subdomain},
        queue=QueueNames.RULES_DELETE,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        error = response.get("error", "Unknown error")
        if error == "Rule not found":
            raise HTTPException(status_code=404, detail=error)
        raise HTTPException(status_code=400, detail=error)

    return DeleteRuleResponse(success=True)


@router.put("/rules/priorities", response_model=UpdatePrioritiesResponse)
async def update_rule_priorities(request: UpdatePrioritiesRequest):
    """
    Обновление приоритетов правил.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    """
    logger.info("HTTP -> RabbitMQ RPC: обновление приоритетов для subdomain=%s", request.subdomain)

    response = await broker.publish(
        request.model_dump(),
        queue=QueueNames.PRIORITIES_UPDATE,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))

    return UpdatePrioritiesResponse(success=True)


@router.post("/leads/styles", response_model=GetStylesResponse)
async def get_leads_styles(request: GetStylesRequest):
    """
    Получение стилей для лидов на основе правил.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    Возвращает только те лиды, которые подходят под правила.
    """
    logger.info(
        "HTTP -> RabbitMQ RPC: получение стилей для %s лидов, subdomain=%s",
        len(request.lead_ids),
        request.subdomain,
    )

    response = await broker.publish(
        request.model_dump(),
        queue=QueueNames.LEADS_STYLES,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))

    # Конвертируем dict в LeadStyle объекты
    styles = {
        lead_id: LeadStyle(**style_data)
        for lead_id, style_data in response.get("styles", {}).items()
    }

    return GetStylesResponse(styles=styles)


@router.post("/rules/test", response_model=TestRuleResponse)
async def test_rule(request: TestRuleRequest):
    """
    Тестирование правила на конкретных данных лида.

    Отправляет запрос в очередь RabbitMQ и ждёт ответа от worker'а.
    Используется для отладки и проверки условий.
    """
    logger.info("HTTP -> RabbitMQ RPC: тестирование правила")

    response = await broker.publish(
        {
            "conditions": request.conditions.model_dump(),
            "lead_data": request.lead_data,
        },
        queue=QueueNames.RULES_TEST,
        rpc=True,
        rpc_timeout=RPC_TIMEOUT,
    )

    if not response.get("success"):
        raise HTTPException(status_code=400, detail=response.get("error", "Unknown error"))

    return TestRuleResponse(
        matches=response["matches"],
        details=response.get("details", ""),
    )
