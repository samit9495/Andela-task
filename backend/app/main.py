"""FastAPI application factory, lifespan, and global exception handlers."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.routes import events, health, incidents, metrics, risk_score
from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    DomainError,
    EventValidationError,
    IncidentNotFound,
    LLMResponseInvalid,
    LLMTimeout,
    TriageFailed,
)
from backend.app.core.logging import configure_logging
from backend.app.db.init_db import init_db

logger = logging.getLogger(__name__)

_DOMAIN_ERROR_RESPONSES: dict[type[DomainError], tuple[int, str]] = {
    EventValidationError: (422, "event_validation_error"),
    IncidentNotFound: (404, "incident_not_found"),
    TriageFailed: (503, "triage_failed"),
    LLMTimeout: (504, "llm_timeout"),
    LLMResponseInvalid: (502, "llm_response_invalid"),
}
_DOMAIN_ERROR_DEFAULT = (400, "domain_error")


async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """Translate a domain exception into a sanitized JSON response."""
    status_code, code = _DOMAIN_ERROR_RESPONSES.get(type(exc), _DOMAIN_ERROR_DEFAULT)
    detail = str(exc) or code.replace("_", " ")
    return JSONResponse(status_code=status_code, content={"detail": detail, "code": code})


async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    """Return a sanitized 500 for any unhandled exception."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, handle_unexpected)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(events.router)
    app.include_router(metrics.router)
    app.include_router(incidents.router)
    app.include_router(risk_score.router)
    return app


app = create_app()
