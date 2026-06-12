"""
Security utilities for the AutoForge Backend.

Provides:
  - API key validation dependency
  - CORS configuration helper
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.core.config import get_settings

settings = get_settings()

_api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """
    FastAPI dependency that validates the ``X-API-Key`` header.

    Returns the validated key on success; raises 401 on failure.
    """
    if api_key is None or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
    return api_key
