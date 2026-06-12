"""
Constants and configuration for the AutoForge Smart Manufacturing Plant Simulator.

All configurable parameters for Phases 1 and 2 are centralised here.
"""
import os
from pathlib import Path

# Load .env from the project root (two levels up from this file)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(dotenv_path=_env_path, override=False)
except ImportError:
    pass  # dotenv not installed; rely on shell environment

# ---------------------------------------------------------------------------
# Factory Identity
# ---------------------------------------------------------------------------
FACTORY_ID = os.getenv("FACTORY_ID", "AUTOFORGE_01")

# ---------------------------------------------------------------------------
# Telemetry Settings
# ---------------------------------------------------------------------------
TELEMETRY_INTERVAL_SECONDS = float(os.getenv("TELEMETRY_INTERVAL_SECONDS", "1.0"))
SHUTDOWN_GRACE_PERIOD_SECONDS = float(os.getenv("SHUTDOWN_GRACE_PERIOD_SECONDS", "5.0"))

# ---------------------------------------------------------------------------
# Factory Composition
# ---------------------------------------------------------------------------
FACTORY_COMPOSITION = {
    "conveyor_motor": 4,
    "hydraulic_press": 3,
    "cnc_machine": 3,
    "robotic_arm": 3,
    "industrial_turbine": 2,
    "cooling_system": 3,
    "welding_unit": 3,
    "assembly_robot": 3,
}

# ---------------------------------------------------------------------------
# Machine Statuses
# ---------------------------------------------------------------------------
STATUS_HEALTHY = "healthy"
STATUS_WARNING = "warning"
STATUS_CRITICAL = "critical"
STATUS_OFFLINE = "offline"

# ---------------------------------------------------------------------------
# Probabilities and Simulation Rates
# ---------------------------------------------------------------------------
BASE_ANOMALY_PROBABILITY = float(os.getenv("BASE_ANOMALY_PROBABILITY", "0.01"))
BASE_DEGRADATION_RATE = float(os.getenv("BASE_DEGRADATION_RATE", "0.005"))

# ---------------------------------------------------------------------------
# Phase 2 — Streaming Engine
# ---------------------------------------------------------------------------
STREAM_BUFFER_SIZE = int(os.getenv("STREAM_BUFFER_SIZE", "5000"))
EVENT_RETENTION_SECONDS = int(os.getenv("EVENT_RETENTION_SECONDS", "300"))

# ---------------------------------------------------------------------------
# Phase 2 — Local Event Storage
# ---------------------------------------------------------------------------
LOCAL_STORAGE_ENABLED = os.getenv("LOCAL_STORAGE_ENABLED", "true").lower() == "true"
LOCAL_STORAGE_BASE_DIR = os.getenv("LOCAL_STORAGE_BASE_DIR", "data/raw_stream")
FILE_ROTATION_INTERVAL_SECONDS = int(os.getenv("FILE_ROTATION_INTERVAL_SECONDS", "300"))

# ---------------------------------------------------------------------------
# Phase 2 — Replay Engine
# ---------------------------------------------------------------------------
DEFAULT_REPLAY_SPEED = float(os.getenv("DEFAULT_REPLAY_SPEED", "1.0"))

# ---------------------------------------------------------------------------
# Phase 2 — Correlation Engine
# ---------------------------------------------------------------------------
CORRELATION_ENABLED = os.getenv("CORRELATION_ENABLED", "true").lower() == "true"
MACHINE_INTERACTION_RADIUS = int(os.getenv("MACHINE_INTERACTION_RADIUS", "3"))

# ---------------------------------------------------------------------------
# Phase 2 — Degradation Engine
# ---------------------------------------------------------------------------
DEGRADATION_RECOVERY_PROBABILITY = float(os.getenv("DEGRADATION_RECOVERY_PROBABILITY", "0.002"))
MAINTENANCE_RESET_PROBABILITY = float(os.getenv("MAINTENANCE_RESET_PROBABILITY", "0.001"))

# ---------------------------------------------------------------------------
# Phase 2 — Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_ENABLED = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/autoforge.log")
LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", str(10 * 1024 * 1024)))  # 10 MB
LOG_FILE_BACKUP_COUNT = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))

# ---------------------------------------------------------------------------
# Phase 3 — Ingestion Backend Integration
# ---------------------------------------------------------------------------
INGESTION_API_URL = os.getenv("INGESTION_API_URL", "http://127.0.0.1:8000")
INGESTION_API_KEY = os.getenv("INGESTION_API_KEY", "autoforge-dev-key-2026")
INGESTION_TIMEOUT_SECONDS = int(os.getenv("INGESTION_TIMEOUT_SECONDS", "5"))
INGESTION_RETRY_ATTEMPTS = int(os.getenv("INGESTION_RETRY_ATTEMPTS", "3"))
ENABLE_BACKEND_FORWARDING = os.getenv("ENABLE_BACKEND_FORWARDING", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Phase 4 — Kinesis Data Streams Transport
# ---------------------------------------------------------------------------
KINESIS_FORWARDING_ENABLED = os.getenv("KINESIS_FORWARDING_ENABLED", "true").lower() == "true"
KINESIS_STREAM_NAME = os.getenv("KINESIS_STREAM_NAME", "autoforge-telemetry-stream")
KINESIS_REGION = os.getenv("KINESIS_REGION", "ap-south-1")
KINESIS_MAX_BATCH_SIZE = int(os.getenv("KINESIS_MAX_BATCH_SIZE", "100"))
KINESIS_RETRY_ATTEMPTS = int(os.getenv("KINESIS_RETRY_ATTEMPTS", "3"))
