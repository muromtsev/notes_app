from contextlib import asynccontextmanager

from fastapi import FastAPI
from structlog import get_logger

from notes_app.core.config import settings
from notes_app.core.logging import setup_logging

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    logger.info("app_starting", env=settings.app_env, debug=settings.debug)
    yield
    logger.info("app_stopping")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
