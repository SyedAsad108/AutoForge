"""
Phase 3 test suite for the AutoForge Backend Ingestion API.

Covers:
  - Telemetry endpoint (accept, reject, schema errors, API key)
  - Batch ingestion
  - Validation engine (range checks)
  - Enrichment engine (metadata stamping)
  - Buffering engine (enqueue, overflow)
  - Producer interface / local producer
  - Health, readiness, metrics endpoints
  - Middleware (request IDs)
"""

import asyncio
import os
import sys
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.ingestion.validation_engine import ValidationEngine
from backend.ingestion.enrichment_engine import EnrichmentEngine
from backend.ingestion.buffering_engine import BufferingEngine
from backend.ingestion.local_producer import LocalProducer
from backend.models.telemetry_models import TelemetryEvent

API_KEY = "autoforge-dev-key-2026"
HEADERS = {"X-API-Key": API_KEY}


def _make_event(**overrides) -> dict:
    """Build a valid telemetry event dict."""
    base = {
        "event_id": str(uuid.uuid4()),
        "machine_id": "M001",
        "machine_type": "conveyor_motor",
        "factory_id": "AUTOFORGE_01",
        "timestamp": "2026-04-26T12:00:00Z",
        "status": "healthy",
        "telemetry": {"rpm": 1500.0, "temperature": 45.0, "power_consumption": 5.0},
        "anomaly_detected": False,
        "anomaly_type": None,
        "anomaly_severity": 0.0,
        "degradation_level": 0.0,
    }
    base.update(overrides)
    return base


# ===================================================================
# Telemetry Endpoint
# ===================================================================
class TestTelemetryEndpoint:

    @pytest.mark.asyncio
    async def test_accept_valid_event(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/telemetry", json=_make_event(), headers=HEADERS)
            assert r.status_code == 200
            data = r.json()
            assert data["status"] == "accepted"
            assert data["pipeline_status"] == "buffered"

    @pytest.mark.asyncio
    async def test_reject_bad_machine_type(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ev = _make_event(machine_type="unknown_machine")
            r = await client.post("/telemetry", json=ev, headers=HEADERS)
            assert r.status_code == 422  # Pydantic validation

    @pytest.mark.asyncio
    async def test_reject_bad_status(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ev = _make_event(status="exploded")
            r = await client.post("/telemetry", json=ev, headers=HEADERS)
            assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_reject_out_of_range_telemetry(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ev = _make_event(telemetry={"rpm": 99999, "temperature": -500, "power_consumption": 5.0})
            r = await client.post("/telemetry", json=ev, headers=HEADERS)
            assert r.status_code == 422
            body = r.json()
            assert body["status"] == "rejected"
            assert len(body["errors"]) == 2

    @pytest.mark.asyncio
    async def test_reject_missing_api_key(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/telemetry", json=_make_event())
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_reject_wrong_api_key(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/telemetry", json=_make_event(), headers={"X-API-Key": "bad"})
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_response_has_request_id(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/telemetry", json=_make_event(), headers=HEADERS)
            assert "x-request-id" in r.headers


# ===================================================================
# Batch Ingestion
# ===================================================================
class TestBatchIngestion:

    @pytest.mark.asyncio
    async def test_batch_all_valid(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            batch = {"events": [_make_event() for _ in range(3)]}
            r = await client.post("/telemetry/batch", json=batch, headers=HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["total_accepted"] == 3
            assert body["total_rejected"] == 0

    @pytest.mark.asyncio
    async def test_batch_partial_rejection(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            good = _make_event()
            bad = _make_event(telemetry={"rpm": 99999, "temperature": 45.0, "power_consumption": 5.0})
            batch = {"events": [good, bad]}
            r = await client.post("/telemetry/batch", json=batch, headers=HEADERS)
            body = r.json()
            assert body["status"] == "partial"
            assert body["total_accepted"] == 1
            assert body["total_rejected"] == 1


# ===================================================================
# Validation Engine
# ===================================================================
class TestValidationEngine:

    def test_valid_conveyor(self):
        ev = TelemetryEvent(**_make_event())
        engine = ValidationEngine()
        result = engine.validate(ev)
        assert result.is_valid

    def test_invalid_rpm(self):
        ev = TelemetryEvent(**_make_event(
            telemetry={"rpm": -100, "temperature": 45.0, "power_consumption": 5.0}
        ))
        engine = ValidationEngine()
        result = engine.validate(ev)
        assert not result.is_valid
        assert any("rpm" in e["field"] for e in result.errors)

    def test_valid_cnc(self):
        ev = TelemetryEvent(**_make_event(
            machine_type="cnc_machine",
            telemetry={"spindle_speed": 8000, "temperature": 40, "tool_wear": 50, "vibration": 2}
        ))
        engine = ValidationEngine()
        assert engine.validate(ev).is_valid


# ===================================================================
# Enrichment Engine
# ===================================================================
class TestEnrichmentEngine:

    def test_metadata_added(self):
        engine = EnrichmentEngine()
        event_dict = _make_event()
        enriched = engine.enrich(event_dict, request_id="req-123")
        assert "metadata" in enriched
        assert enriched["metadata"]["request_id"] == "req-123"
        assert enriched["metadata"]["schema_version"] == "v1"
        assert "ingested_at" in enriched["metadata"]


# ===================================================================
# Buffering Engine
# ===================================================================
class TestBufferingEngine:

    @pytest.mark.asyncio
    async def test_enqueue(self):
        producer = LocalProducer()
        buf = BufferingEngine(producer)
        ok = await buf.enqueue({"test": 1})
        assert ok
        assert buf.depth == 1

    @pytest.mark.asyncio
    async def test_metrics(self):
        producer = LocalProducer()
        buf = BufferingEngine(producer)
        await buf.enqueue({"test": 1})
        await buf.enqueue({"test": 2})
        assert buf.total_buffered == 2


# ===================================================================
# Health / Readiness / Metrics Endpoints
# ===================================================================
class TestMonitoringEndpoints:

    @pytest.mark.asyncio
    async def test_health(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/health")
            assert r.status_code == 200
            body = r.json()
            assert body["status"] == "ok"
            assert "uptime_seconds" in body

    @pytest.mark.asyncio
    async def test_ready(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/ready")
            assert r.status_code == 200
            assert r.json()["ready"] is True

    @pytest.mark.asyncio
    async def test_metrics(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/metrics")
            assert r.status_code == 200
            body = r.json()
            assert "total_events_ingested" in body
            assert "events_per_second" in body

    @pytest.mark.asyncio
    async def test_root(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/")
            assert r.status_code == 200
            assert "AutoForge" in r.json()["service"]
