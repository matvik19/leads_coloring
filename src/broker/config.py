"""
Конфигурация RabbitMQ брокера для FastStream.
"""

from src.common.config import RMQ_USER, RMQ_PASSWORD, RMQ_HOST, RMQ_PORT, RMQ_VHOST


# URL подключения к RabbitMQ
RABBITMQ_URL = f"amqp://{RMQ_USER}:{RMQ_PASSWORD}@{RMQ_HOST}:{RMQ_PORT}/{RMQ_VHOST}"

# Названия очередей
class QueueNames:
    """Названия очередей в RabbitMQ."""

    # Основные очереди для окраски лидов
    LEADS_COLORING_STYLES = "leads_coloring_styles"
    LEADS_COLORING_RULES = "leads_coloring_rules"


# Настройки retry
MAX_RETRY_COUNT = 3
RETRY_DELAY = 5  # секунды между попытками

# Настройки prefetch для консьюмеров
PREFETCH_COUNT = 10
