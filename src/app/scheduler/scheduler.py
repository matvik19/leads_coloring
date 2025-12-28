from taskiq.schedule_sources import LabelScheduleSource
from taskiq import TaskiqScheduler
from app.core.broker import broker

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
