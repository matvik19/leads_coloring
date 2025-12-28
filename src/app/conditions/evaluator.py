"""
Evaluator для проверки условий правил окраски лидов.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta
import re

from src.common.log_config import logger


class ConditionEvaluator:
    """
    Класс для проверки условий правил окраски лидов.
    """

    @staticmethod
    def evaluate(conditions: Dict[str, Any], lead_data: Dict[str, Any]) -> bool:
        """
        Проверяет, подходит ли лид под условия.

        Args:
            conditions: Условия в формате {"type": "AND"|"OR", "rules": [...]}
            lead_data: Данные лида для проверки

        Returns:
            bool: True если лид подходит под условия
        """
        condition_type = conditions.get("type", "AND")
        rules = conditions.get("rules", [])

        if not rules:
            return False

        results = []
        for rule in rules:
            result = ConditionEvaluator._evaluate_single_rule(rule, lead_data)
            results.append(result)

        if condition_type == "AND":
            return all(results)
        else:  # OR
            return any(results)

    @staticmethod
    def _evaluate_single_rule(rule: Dict[str, Any], lead_data: Dict[str, Any]) -> bool:
        """
        Проверяет одно правило.

        Args:
            rule: Правило {"field": "...", "operator": "...", "value": "..."}
            lead_data: Данные лида

        Returns:
            bool: True если правило выполнено
        """
        field = rule.get("field")
        operator = rule.get("operator")
        expected_value = rule.get("value")

        # Получаем значение поля из данных лида
        actual_value = ConditionEvaluator._get_field_value(field, lead_data)

        # Проверяем условие в зависимости от оператора
        return ConditionEvaluator._check_condition(
            actual_value, operator, expected_value
        )

    @staticmethod
    def _get_field_value(field: str, lead_data: Dict[str, Any]) -> Any:
        """
        Извлекает значение поля из данных лида.

        Args:
            field: Название поля
            lead_data: Данные лида

        Returns:
            Значение поля или None
        """
        # Сначала проверяем стандартные поля
        if field in lead_data:
            return lead_data[field]

        # Проверяем кастомные поля
        custom_fields = lead_data.get("custom_fields_values", [])
        for cf in custom_fields:
            if cf.get("field_id") == field or cf.get("field_code") == field:
                values = cf.get("values", [])
                if values:
                    return values[0].get("value")

        return None

    @staticmethod
    def _check_condition(actual_value: Any, operator: str, expected_value: Any) -> bool:
        """
        Проверяет условие.

        Args:
            actual_value: Фактическое значение
            operator: Оператор сравнения
            expected_value: Ожидаемое значение

        Returns:
            bool: True если условие выполнено
        """
        # Обработка пустых значений
        if operator == "is_empty":
            return actual_value is None or actual_value == "" or actual_value == []

        if operator == "is_not_empty":
            return actual_value is not None and actual_value != "" and actual_value != []

        # Если actual_value None, и это не проверка на пустоту
        if actual_value is None:
            return False

        # Текстовые операторы
        if operator == "equals":
            return str(actual_value).lower() == str(expected_value).lower()

        if operator == "not_equals":
            return str(actual_value).lower() != str(expected_value).lower()

        if operator == "contains":
            return str(expected_value).lower() in str(actual_value).lower()

        if operator == "not_contains":
            return str(expected_value).lower() not in str(actual_value).lower()

        if operator == "starts_with":
            return str(actual_value).lower().startswith(str(expected_value).lower())

        if operator == "ends_with":
            return str(actual_value).lower().endswith(str(expected_value).lower())

        # Числовые операторы
        try:
            if operator == "greater_than":
                return float(actual_value) > float(expected_value)

            if operator == "less_than":
                return float(actual_value) < float(expected_value)

            if operator == "greater_or_equal":
                return float(actual_value) >= float(expected_value)

            if operator == "less_or_equal":
                return float(actual_value) <= float(expected_value)

            if operator == "between":
                # expected_value должен быть списком [min, max]
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    return float(expected_value[0]) <= float(actual_value) <= float(expected_value[1])
                return False
        except (ValueError, TypeError):
            # Если не удается преобразовать в число
            logger.warning(
                "Не удалось преобразовать значения в числа для оператора %s: %s, %s",
                operator, actual_value, expected_value
            )
            return False

        # Операторы для списков (enum)
        if operator == "in_list":
            # expected_value должен быть списком
            if isinstance(expected_value, list):
                return str(actual_value) in [str(v) for v in expected_value]
            return str(actual_value) == str(expected_value)

        if operator == "not_in_list":
            # expected_value должен быть списком
            if isinstance(expected_value, list):
                return str(actual_value) not in [str(v) for v in expected_value]
            return str(actual_value) != str(expected_value)

        # Операторы для дат
        if operator in ["after", "before", "today", "yesterday", "this_week", "last_week",
                        "this_month", "last_month", "last_n_days"]:
            return ConditionEvaluator._check_date_condition(actual_value, operator, expected_value)

        logger.warning("Неизвестный оператор: %s", operator)
        return False

    @staticmethod
    def _check_date_condition(actual_value: Any, operator: str, expected_value: Any) -> bool:
        """
        Проверяет условие для дат.

        Args:
            actual_value: Значение даты (timestamp или строка)
            operator: Оператор сравнения
            expected_value: Ожидаемое значение

        Returns:
            bool: True если условие выполнено
        """
        try:
            # Преобразуем actual_value в datetime
            if isinstance(actual_value, int):
                actual_date = datetime.fromtimestamp(actual_value)
            elif isinstance(actual_value, str):
                # Пытаемся распарсить строку
                actual_date = datetime.fromisoformat(actual_value.replace('Z', '+00:00'))
            elif isinstance(actual_value, datetime):
                actual_date = actual_value
            else:
                return False

            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            if operator == "today":
                return actual_date.date() == today.date()

            if operator == "yesterday":
                yesterday = today - timedelta(days=1)
                return actual_date.date() == yesterday.date()

            if operator == "this_week":
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=7)
                return week_start <= actual_date < week_end

            if operator == "last_week":
                week_start = today - timedelta(days=today.weekday() + 7)
                week_end = week_start + timedelta(days=7)
                return week_start <= actual_date < week_end

            if operator == "this_month":
                month_start = today.replace(day=1)
                if today.month == 12:
                    month_end = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    month_end = today.replace(month=today.month + 1, day=1)
                return month_start <= actual_date < month_end

            if operator == "last_month":
                if today.month == 1:
                    month_start = today.replace(year=today.year - 1, month=12, day=1)
                    month_end = today.replace(month=1, day=1)
                else:
                    month_start = today.replace(month=today.month - 1, day=1)
                    month_end = today.replace(day=1)
                return month_start <= actual_date < month_end

            if operator == "last_n_days":
                # expected_value - количество дней
                days_ago = today - timedelta(days=int(expected_value))
                return days_ago <= actual_date <= now

            if operator == "after":
                # expected_value - дата для сравнения
                if isinstance(expected_value, str):
                    expected_date = datetime.fromisoformat(expected_value.replace('Z', '+00:00'))
                elif isinstance(expected_value, int):
                    expected_date = datetime.fromtimestamp(expected_value)
                else:
                    return False
                return actual_date > expected_date

            if operator == "before":
                # expected_value - дата для сравнения
                if isinstance(expected_value, str):
                    expected_date = datetime.fromisoformat(expected_value.replace('Z', '+00:00'))
                elif isinstance(expected_value, int):
                    expected_date = datetime.fromtimestamp(expected_value)
                else:
                    return False
                return actual_date < expected_date

            return False

        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Ошибка при проверке даты: %s", e)
            return False


def evaluate_conditions(conditions: Dict[str, Any], lead_data: Dict[str, Any]) -> bool:
    """
    Удобная функция для проверки условий.

    Args:
        conditions: Условия правила
        lead_data: Данные лида

    Returns:
        bool: True если лид подходит под условия
    """
    return ConditionEvaluator.evaluate(conditions, lead_data)
