import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.app.core.logging import setup_logging, logger
from src.app.api.api_v1.api import api_router
from src.app.db.async_session import wait_for_db, run_migrations

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


app = FastAPI(title="Leads Coloring Widget", lifespan=lifespan)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
