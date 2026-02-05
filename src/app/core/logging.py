import logging
import sys
from contextvars import ContextVar
import logging_loki

subdomain_var: ContextVar[str] = ContextVar("subdomain", default="unknown")
request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")


class ContextFilter(logging.Filter):
    """Добавляет subdomain и request_id в каждую запись лога"""

    def filter(self, record):
        record.subdomain = subdomain_var.get()
        record.request_id = request_id_var.get()
        return True


def setup_logging(
    service_name: str = "leads-coloring", environment: str = "production"
):
    """
    Настраивает логирование один раз при старте приложения
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.handlers.clear()

    context_filter = ContextFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(subdomain)s] [%(request_id)s] %(asctime)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(context_filter)
    logger.addHandler(console_handler)

    loki_handler = logging_loki.LokiHandler(
        url="http://loki:3100/loki/api/v1/push",
        tags={
            "service": service_name,
            "environment": environment,
        },
        version="1",
    )
    loki_handler.setLevel(logging.INFO)
    loki_formatter = logging.Formatter(
        "%(subdomain)s | %(request_id)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s"
    )
    loki_handler.setFormatter(loki_formatter)
    loki_handler.addFilter(context_filter)
    logger.addHandler(loki_handler)

    # Отключаем DEBUG логи от сторонних библиотек
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiormq").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("faststream").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    logging.info("Logging configured for service: %s", service_name)


# Используем root логгер, чтобы ContextFilter работал везде
logger = logging.getLogger()
