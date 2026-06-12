"""
Structured logging for the AutoForge simulator.

Supports:
  • Console (stdout) handler
  • Optional RotatingFileHandler (configurable via constants)
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from simulator.utils.constants import (
    LOG_LEVEL,
    LOG_FILE_ENABLED,
    LOG_FILE_PATH,
    LOG_FILE_MAX_BYTES,
    LOG_FILE_BACKUP_COUNT,
)

_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


def setup_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger.

    On the first call for a given *name* the logger is set up with:
      - a ``StreamHandler`` writing to stdout
      - an optional ``RotatingFileHandler`` (if ``LOG_FILE_ENABLED`` is true)
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FMT)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional rotating file handler
        if LOG_FILE_ENABLED:
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE_PATH,
                maxBytes=LOG_FILE_MAX_BYTES,
                backupCount=LOG_FILE_BACKUP_COUNT,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

