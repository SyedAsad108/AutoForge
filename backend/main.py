"""
AutoForge Ingestion API -- FastAPI application entry point.

Assembles routes, middleware, exception handlers, CORS, and the
background ingestion buffer drain loop.

Run with:
    uvicorn backend.main:app --reload
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.dependencies import get_ingestion_service
from backend.api.routes import health, metrics, telemetry, analytics_router
from backend.core.config import get_settings
from backend.core.logger import get_logger
from backend.middleware.exception_handlers import register_exception_handlers
from backend.middleware.logging_middleware import LoggingMiddleware
from backend.middleware.request_id import RequestIdMiddleware
from backend.services.background_metrics_worker import worker

logger = get_logger("Main")
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan handler (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background tasks tied to the application lifecycle."""
    ingestion = get_ingestion_service()

    # Start the buffer drain loop as a background task
    drain_task = asyncio.create_task(ingestion.buffer.start_drain_loop())
    
    # Start the background metrics worker
    await worker.start()
    
    logger.info(
        f"[STARTUP] {settings.APP_NAME} v{settings.APP_VERSION} "
        f"node={settings.BACKEND_NODE_ID}"
    )
    yield

    # Shutdown
    logger.info("[SHUTDOWN] Initializing graceful shutdown...")
    
    # 1. Stop the drain loop signal
    ingestion.buffer.stop()
    
    # 2. Wait for the drain task to complete (it should drain the queue)
    logger.info("[SHUTDOWN] Waiting for ingestion buffer to drain...")
    try:
        # Give it a timeout to prevent hanging forever
        await asyncio.wait_for(drain_task, timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("[SHUTDOWN] Drain task timed out. Forcing cancellation...")
        drain_task.cancel()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"[SHUTDOWN] Error during drain task shutdown: {e}")

    # 3. Final cleanup of services
    ingestion.close()
    await worker.stop()
    logger.info("[SHUTDOWN] Ingestion API shutdown complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Industrial telemetry ingestion gateway for the AutoForge "
        "Smart Manufacturing Plant.  Receives, validates, enriches, "
        "and buffers real-time machine telemetry events."
    ),
    lifespan=lifespan,
)

# --- Middleware (order matters: outermost first) ---
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception handlers ---
register_exception_handlers(app)

# --- Routes ---
app.include_router(telemetry.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(analytics_router.router)




@app.get("/", tags=["Root"], summary="API root")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
