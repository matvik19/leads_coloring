import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.common.database import wait_for_db, run_migrations
from src.common.log_config import setup_logging, logger
from src.rules.routers import router as rules_router

setup_logging(service_name="leads-coloring", environment="production")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом FastAPI (миграции БД)."""
    await wait_for_db()
    await run_migrations()
    logger.info("FastAPI приложение готово к работе.")

    try:
        yield
    finally:
        logger.info("FastAPI приложение останавливается...")


app = FastAPI(title="AMOCRM Leads Coloring Widget", lifespan=lifespan)

app.include_router(rules_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "leads-coloring"}


@app.post("/test_log")
def test_log():
    logger.info("Тест с библиотекой!")
    logger.error("Ошибка с библиотекой!")
    return {"status": "logged"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
