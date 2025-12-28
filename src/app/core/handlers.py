import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

logger = logging.getLogger("app_logger")

async def pydantic_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Перехватывает ошибки Pydantic и логирует их."""
    error = jsonable_encoder(exc.errors())
    logger.exception("Ошибка в Pydantic схеме: %s", error)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error},
    )