"""
Structured logging for the AutoForge Backend.

Provides a configured logger with console and optional rotating-file handlers.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from backend.core.config import get_settings

_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the backend."""
    settings = get_settings()
    logger = logging.getLogger(f"backend.{name}")
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FMT)

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        logger.addHandler(console)

        if settings.LOG_FILE_ENABLED:
            os.makedirs(os.path.dirname(settings.LOG_FILE_PATH), exist_ok=True)
            fh = RotatingFileHandler(
                settings.LOG_FILE_PATH,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger
