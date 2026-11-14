"""Точка входа corp-ext.

Публичный API живёт под ``/corp/api`` (за nginx), служебные ручки для nginx —
под ``/internal`` (наружу не публикуются), ``/health`` и ``/metrics`` — для compose и Prometheus.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger

API_PREFIX = "/corp/api"

try:
    APP_VERSION = version("corp-ext")
except PackageNotFoundError:  # проект не устанавливается как пакет (tool.uv.package = false)
    APP_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log)

    docs_enabled = settings.env != "prod"
    app = FastAPI(
        title="corp-ext",
        version=APP_VERSION,
        openapi_url=f"{API_PREFIX}/openapi.json" if docs_enabled else None,
        docs_url=f"{API_PREFIX}/docs" if docs_enabled else None,
        redoc_url=None,
    )

    @app.get("/health", response_model=HealthResponse, tags=["service"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service="corp-ext", version=APP_VERSION)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    api = APIRouter(prefix=API_PREFIX)

    @api.get("/version", response_model=HealthResponse, tags=["service"])
    async def api_version() -> HealthResponse:
        return HealthResponse(status="ok", service="corp-ext", version=APP_VERSION)

    # Роутеры модулей подключаются здесь по мере реализации этапов (SPEC §21).
    app.include_router(api)

    get_logger(__name__).info("app_created", env=settings.env, docs=docs_enabled)
    return app


def app_factory() -> FastAPI:
    """Для ``uvicorn app.main:app_factory --factory``."""
    return create_app()
