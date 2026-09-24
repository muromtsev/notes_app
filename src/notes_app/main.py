from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from structlog import get_logger

from notes_app.api.v1.router import api_router
from notes_app.core.config import settings
from notes_app.core.exceptions import AppError
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

app.include_router(api_router)

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Единый формат ошибок для всех доменных исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

