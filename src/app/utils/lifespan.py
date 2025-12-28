from logging import config
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.broker import broker
from app.core.logging import logging_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.dictConfig(logging_config)
    await broker.startup()
    yield
    await broker.shutdown()
