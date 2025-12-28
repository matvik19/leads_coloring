import typing
from taskiq import TaskiqMiddleware, TaskiqMessage
from app.core.context import message_id


class LogMiddleware(TaskiqMiddleware):
    async def pre_execute(
        self,
        message: TaskiqMessage,
    ) -> TaskiqMessage | typing.Coroutine[typing.Any, typing.Any, TaskiqMessage]:

        message_id.set(message.task_id)

        return message
