"""
Global exception handlers for the AutoForge backend.

Catches unhandled exceptions and Pydantic validation errors,
returning structured JSON error responses.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.core.logger import get_logger

logger = get_logger("ExceptionHandler")


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Convert error details to JSON-safe dicts
        safe_errors = []
        for err in exc.errors():
            safe_err = {
                "type": str(err.get("type", "")),
                "loc": list(err.get("loc", [])),
                "msg": str(err.get("msg", "")),
            }
            safe_errors.append(safe_err)
        logger.warning(f"[VALIDATION] Schema error: {safe_errors}")
        return JSONResponse(
            status_code=422,
            content={
                "status": "rejected",
                "detail": "Telemetry schema validation failed",
                "errors": safe_errors,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(f"[ERROR] Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": "Internal server error",
            },
        )
