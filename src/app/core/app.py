from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette_context import plugins
from starlette_context.middleware import RawContextMiddleware

from app.core.settings import config
from app.api.api_v1.api import api_router
from app.utils.lifespan import lifespan
from app.core.handlers import pydantic_error_handler

def create_app() -> FastAPI:
    current_app = FastAPI(
        lifespan=lifespan,
        title=config.app_cfg.PROJECT_NAME,
        openapi_url=config.app_cfg.OPENAPI_PATH
    )
    current_app.add_middleware(RawContextMiddleware, plugins=(plugins.RequestIdPlugin(),))

    current_app.add_exception_handler(RequestValidationError, pydantic_error_handler)

    current_app.include_router(api_router, prefix=f"/api/v1{config.app_cfg.NAMESPACE}")
    return current_app
