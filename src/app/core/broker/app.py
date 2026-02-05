"""
Конфигурация FastStream RabbitMQ брокера.
"""

from faststream.rabbit import RabbitBroker, Channel

from app.core.settings import config
from app.core.logging import logger
from app.core.broker.middlewares.logging_middleware import LoggingMiddleware
from app.core.broker.middlewares.retry_middleware import RetryMiddleware
from app.core.broker.routers.rules import rules_router
from app.core.broker.routers.leads import leads_router
from app.core.broker.routers.health import health_router


# Основной брокер для получения сообщений (subscribers)
broker = RabbitBroker(
    url=config.rabbit_cfg.rabbitmq_uri,
    logger=logger,
    middlewares=[
        RetryMiddleware,  # Сначала retry (внешний слой)
        LoggingMiddleware,  # Потом logging (внутренний слой)
    ],
    default_channel=Channel(prefetch_count=config.worker_cfg.PREFETCH_COUNT),
)

# Подключаем роутеры для обработки сообщений из RabbitMQ
broker.include_router(rules_router)
broker.include_router(leads_router)
broker.include_router(health_router)
