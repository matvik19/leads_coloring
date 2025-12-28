from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.core.settings import config
from app.api.api_v1.api import api_router
from app.utils.lifespan import lifespan
from app.core.handlers import pydantic_error_handler


def create_app() -> FastAPI:
    current_app = FastAPI(
        lifespan=lifespan,
        title=config.app_cfg.PROJECT_NAME,
        description=config.app_cfg.PROJECT_DESC,
        version=config.app_cfg.VERSION,
        openapi_url=config.app_cfg.OPENAPI_PATH
    )

    # CORS middleware
    current_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    current_app.add_exception_handler(RequestValidationError, pydantic_error_handler)

    current_app.include_router(api_router, prefix=f"/api/v1{config.app_cfg.NAMESPACE}")

    return current_app
