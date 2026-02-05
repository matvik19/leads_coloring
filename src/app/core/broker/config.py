"""
Конфигурация имен очередей RabbitMQ для FastStream.
"""


class QueueNames:
    """Имена очередей для обработки операций с правилами окраски"""

    # Операции с правилами
    RULES_CREATE = "leads_coloring_rules_create"
    RULES_UPDATE = "leads_coloring_rules_update"
    RULES_LIST = "leads_coloring_rules_list"
    RULES_DELETE = "leads_coloring_rules_delete"
    RULES_TEST = "leads_coloring_rules_test"

    # Операции с приоритетами
    PRIORITIES_UPDATE = "leads_coloring_priorities_update"

    # Операции с лидами
    LEADS_STYLES = "leads_coloring_leads_styles"

    # Healthcheck
    HEALTH = "leads_coloring_health"


# Настройки retry и prefetch
MAX_RETRY_COUNT = 3
RETRY_DELAY = 5  # секунды
PREFETCH_COUNT = 10  # по умолчанию
