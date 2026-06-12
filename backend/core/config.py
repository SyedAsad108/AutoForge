"""
Centralised configuration for the AutoForge Backend Ingestion API.

All settings are read from environment variables with sensible defaults
for local development.
"""

import os
from functools import lru_cache


class Settings:
    """Application-wide settings loaded from environment."""

    # --- Identity ---
    APP_NAME: str = "AutoForge Ingestion API"
    APP_VERSION: str = "0.3.0"
    BACKEND_NODE_ID: str = os.getenv("BACKEND_NODE_ID", "ingestion-node-01")
    FACTORY_ID: str = os.getenv("FACTORY_ID", "AUTOFORGE_01")

    # --- Server ---
    HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # --- Security ---
    API_KEY: str = os.getenv("API_KEY", "autoforge-dev-key-2026")
    API_KEY_HEADER: str = "X-API-Key"
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # --- Ingestion Buffer ---
    INGESTION_BUFFER_SIZE: int = int(os.getenv("INGESTION_BUFFER_SIZE", "10000"))
    INGESTION_BATCH_SIZE: int = int(os.getenv("INGESTION_BATCH_SIZE", "100"))

    # --- Producer ---
    PRODUCER_TYPE: str = os.getenv("PRODUCER_TYPE", "local")  # local | kinesis (future)
    LOCAL_INGESTION_DIR: str = os.getenv("LOCAL_INGESTION_DIR", "data/ingestion")
    INGESTION_ROTATION_SECONDS: int = int(os.getenv("INGESTION_ROTATION_SECONDS", "300"))

    # --- Retry ---
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "0.5"))
    RETRY_MAX_DELAY: float = float(os.getenv("RETRY_MAX_DELAY", "10.0"))

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE_ENABLED: bool = os.getenv("BACKEND_LOG_FILE_ENABLED", "true").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("BACKEND_LOG_FILE_PATH", "logs/backend.log")

    # --- Schema ---
    SCHEMA_VERSION: str = "v1"

    # --- AWS & Athena ---
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
    ATHENA_DATABASE: str = os.getenv("ATHENA_DATABASE", "autoforge_analytics")
    ATHENA_WORKGROUP: str = os.getenv("ATHENA_WORKGROUP", "autoforge-analytics")


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of Settings."""
    return Settings()
