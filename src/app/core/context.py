"""
Модуль с контекстными переменными для асинхронных потоков
message_id - id таски taskiq, используется в логгере
"""

from contextvars import ContextVar


message_id: ContextVar[str] = ContextVar("message_id", default=None)
