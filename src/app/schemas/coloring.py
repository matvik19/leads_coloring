"""Pydantic схемы для правил окраски"""
from typing import List, Optional, Literal, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class ConditionRule(BaseModel):
    """Одно условие в правиле"""
    field: str = Field(..., description="Название поля для проверки")
    operator: str = Field(..., description="Оператор сравнения")
    value: Any = Field(..., description="Значение для сравнения")


class Conditions(BaseModel):
    """Набор условий с логическим оператором"""
    type: Literal["AND", "OR"] = Field(..., description="Тип логического оператора")
    rules: List[ConditionRule] = Field(..., description="Список правил")


class Style(BaseModel):
    """Стили для окраски лида"""
    text_color: str = Field(..., description="Цвет текста в формате HEX")
    background_color: str = Field(..., description="Цвет фона в формате HEX")


class CreateRuleRequest(BaseModel):
    """Запрос на создание правила"""
    subdomain: str = Field(..., description="Субдомен AmoCRM")
    name: str = Field(..., description="Название правила")
    is_active: bool = Field(default=True, description="Активно ли правило")
    priority: int = Field(default=0, description="Приоритет правила (выше = важнее)")
    conditions: Conditions = Field(..., description="Условия применения правила")
    style: Style = Field(..., description="Стили для применения")


class UpdateRuleRequest(BaseModel):
    """Запрос на обновление правила"""
    subdomain: str = Field(..., description="Субдомен AmoCRM")
    name: Optional[str] = Field(None, description="Название правила")
    is_active: Optional[bool] = Field(None, description="Активно ли правило")
    priority: Optional[int] = Field(None, description="Приоритет правила")
    conditions: Optional[Conditions] = Field(None, description="Условия применения правила")
    style: Optional[Style] = Field(None, description="Стили для применения")


class RuleResponse(BaseModel):
    """Ответ с данными правила"""
    id: int
    name: str
    is_active: bool
    priority: int
    conditions: Dict[str, Any]
    style: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RulesListResponse(BaseModel):
    """Ответ со списком правил"""
    rules: List[RuleResponse]


class CreateRuleResponse(BaseModel):
    """Ответ на создание правила"""
    id: int
    success: bool


class DeleteRuleResponse(BaseModel):
    """Ответ на удаление правила"""
    success: bool


class PriorityUpdate(BaseModel):
    """Обновление приоритета одного правила"""
    id: int
    priority: int


class UpdatePrioritiesRequest(BaseModel):
    """Запрос на обновление приоритетов"""
    subdomain: str
    priorities: List[PriorityUpdate]


class UpdatePrioritiesResponse(BaseModel):
    """Ответ на обновление приоритетов"""
    success: bool


class LeadStyle(BaseModel):
    """Стиль для одного лида"""
    text_color: str
    background_color: str
    matched_rule_id: int
    matched_rule_name: str


class GetStylesRequest(BaseModel):
    """Запрос на получение стилей для лидов"""
    subdomain: str = Field(..., description="Субдомен AmoCRM")
    lead_ids: List[int] = Field(..., description="Список ID лидов")
    access_token: str = Field(..., description="Токен доступа к AmoCRM API")


class GetStylesResponse(BaseModel):
    """Ответ со стилями для лидов"""
    styles: Dict[str, LeadStyle] = Field(
        ...,
        description="Словарь {lead_id: style}. Только лиды, подходящие под правила"
    )


class TestRuleRequest(BaseModel):
    """Запрос на тестирование правила"""
    conditions: Conditions = Field(..., description="Условия для тестирования")
    lead_data: Dict[str, Any] = Field(..., description="Данные лида для проверки")


class TestRuleResponse(BaseModel):
    """Ответ на тестирование правила"""
    matches: bool = Field(..., description="Подходит ли лид под условия")
    details: str = Field(..., description="Детали проверки")


class DealField(BaseModel):
    """Поле сделки для фронтенда"""
    id: str = Field(..., description="ID поля")
    name: str = Field(..., description="Название поля")
    type: str = Field(..., description="Тип поля (string, number, date, enum, boolean)")


class GetDealFieldsResponse(BaseModel):
    """Ответ со списком полей сделок"""
    fields: List[DealField]
