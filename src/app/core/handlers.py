from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def pydantic_error_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic"""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
