"""
Конфигурация RabbitMQ брокера и роутеров.
"""

from faststream.rabbit import RabbitBroker, Channel

from src.common.log_config import logger
from src.broker.config import RABBITMQ_URL, PREFETCH_COUNT
from src.broker.middlewares.logging_middleware import LoggingMiddleware
from src.broker.middlewares.retry_middleware import RetryMiddleware


# Создаем RabbitMQ брокер с настройками
broker = RabbitBroker(
    url=RABBITMQ_URL,
    logger=logger,
    middlewares=[
        RetryMiddleware,  # Сначала retry (внешний слой)
        LoggingMiddleware,  # Потом logging (внутренний слой)
    ],
    default_channel=Channel(prefetch_count=PREFETCH_COUNT),
)

# Здесь можно добавить роутеры для обработки сообщений из RabbitMQ
# Например:
# from src.broker.routers.coloring import coloring_router
# broker.include_router(coloring_router)
