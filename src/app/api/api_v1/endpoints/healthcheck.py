import logging
from fastapi import APIRouter, status

logger = logging.getLogger("app_logger")
router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
async def test_healthcheck():
    logger.debug("Проверка доступности сервиса")
    return {"status": "ok"}
