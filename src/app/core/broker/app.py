from taskiq_aio_pika import AioPikaBroker
from taskiq import TaskiqEvents, TaskiqState
from app.core.settings import config
from app.db import async_session
from .middlewares.message_id import LogMiddleware


broker = AioPikaBroker(
    config.rabbit_cfg.rabbitmq_uri,
    exchange_name="default",
    queue_name="default",
    delayed_message_exchange_plugin=True,
).with_middlewares(LogMiddleware())


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    state.sqldb_session = async_session


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    del state.sqldb_session
