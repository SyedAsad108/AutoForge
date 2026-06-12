"""
Metadata enrichment engine for the AutoForge ingestion pipeline.

Stamps every accepted event with server-side processing context
before it enters the producer pipeline.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict

from backend.core.config import get_settings
from backend.core.logger import get_logger

logger = get_logger("EnrichmentEngine")
settings = get_settings()


class EnrichmentEngine:
    """
    Enriches a validated telemetry event dict with ingestion metadata.
    """

    def enrich(
        self,
        event_dict: Dict[str, Any],
        request_id: str,
    ) -> Dict[str, Any]:
        """
        Add server-side metadata to the event.

        The original event is mutated in-place and also returned.
        """
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        event_dict["metadata"] = {
            "ingested_at": now,
            "request_id": request_id,
            "backend_node": settings.BACKEND_NODE_ID,
            "ingestion_source": "api",
            "schema_version": settings.SCHEMA_VERSION,
        }
        return event_dict
