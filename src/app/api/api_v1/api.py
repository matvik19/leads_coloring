from fastapi import APIRouter

from app.api.api_v1.endpoints.healthcheck import router as healthcheck_router


api_router = APIRouter()
api_router.include_router(healthcheck_router)
