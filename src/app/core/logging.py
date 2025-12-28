import logging
import logging.config
from starlette_context import context
from .context import message_id
from .settings import config


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if context.exists() and "X-Request-ID" in context.data:
            record.request_id = context["X-Request-ID"]
        else:
            record.request_id = None
        return True


class TaskIdFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = message_id.get()
        return True


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "request_id": {
            "format": "%(asctime)s %(levelname)-8s %(name)-24s %(request_id)-8s %(message)s"
        },
    },
    "handlers": {
        "web_stdout": {
            "level": getattr(logging, config.app_cfg.LOGLEVEL, logging.INFO),
            "class": "logging.StreamHandler",
            "formatter": "request_id",
            "filters": [RequestIdFilter()],
        },
        "web_file": {
            "level": getattr(logging, config.app_cfg.LOGLEVEL, logging.INFO),
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "request_id",
            "filters": [RequestIdFilter()],
            "filename": "/logs/web.log",
            "maxBytes": 536870912,
            "backupCount": 10,
        },
        "worker_file": {
            "level": getattr(logging, config.app_cfg.LOGLEVEL, logging.INFO),
            "formatter": "request_id",
            "filters": [TaskIdFilter()],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/logs/worker.log",
            "maxBytes": 536870912,
            "backupCount": 10,
        },
        "worker_stdout": {
            "level": getattr(logging, config.app_cfg.LOGLEVEL, logging.INFO),
            "class": "logging.StreamHandler",
            "formatter": "request_id",
            "filters": [TaskIdFilter()],
        },
        "scheduler_file": {
            "level": getattr(logging, config.app_cfg.LOGLEVEL, logging.INFO),
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/logs/scheduler.log",
            "maxBytes": 536870912,
            "backupCount": 10,
        },
        "scheduler_stdout": {
            "level": getattr(logging, config.app_cfg.LOGLEVEL, logging.INFO),
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "app_logger": {
            "handlers": ["web_stdout", "web_file"],
            "level": config.app_cfg.LOGLEVEL,
        },
        "uvicorn": {"handlers": ["web_stdout", "web_file"], "level": config.app_cfg.LOGLEVEL},
        "uvicorn.error": {"handlers": ["web_stdout", "web_file"], "level": config.app_cfg.LOGLEVEL},
        "uvicorn.access": {
            "handlers": ["web_stdout", "web_file"],
            "level": config.app_cfg.LOGLEVEL,
            "propagate": False,
        },
        "sqlalchemy.engine.Engine": {"handlers": ["web_stdout"], "level": config.app_cfg.LOGLEVEL},
        "worker": {
            "handlers": ["worker_file", "worker_stdout"],
            "level": config.app_cfg.LOGLEVEL,
        },
        "scheduler": {
            "handlers": ["scheduler_file", "scheduler_stdout"],
            "level": config.app_cfg.LOGLEVEL,
        },
    },
}
