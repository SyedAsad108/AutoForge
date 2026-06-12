import asyncio
import httpx
from typing import Dict, Any, List
from simulator.utils.logger import setup_logger
from simulator.utils.constants import (
    INGESTION_API_URL,
    INGESTION_API_KEY,
    INGESTION_TIMEOUT_SECONDS,
    INGESTION_RETRY_ATTEMPTS
)

logger = setup_logger("TelemetryClient")

class TelemetryAPIClient:
    """
    Async HTTP client for forwarding telemetry to the FastAPI backend.
    """
    def __init__(self):
        self.base_url = INGESTION_API_URL.rstrip('/')
        self.timeout = httpx.Timeout(INGESTION_TIMEOUT_SECONDS)
        headers = {"X-API-Key": INGESTION_API_KEY} if INGESTION_API_KEY else {}
        self.client = httpx.AsyncClient(timeout=self.timeout, headers=headers)
        self.retries = INGESTION_RETRY_ATTEMPTS
        logger.info(f"[TRANSPORT] Initialized Telemetry API Client with URL: {self.base_url}")

    async def _send_request(self, endpoint: str, payload: Any) -> bool:
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, self.retries + 1):
            try:
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"[TRANSPORT] HTTP error {e.response.status_code} sending to {url}: {e.response.text}")
                if 400 <= e.response.status_code < 500:
                    return False
            except httpx.RequestError as e:
                logger.warning(f"[TRANSPORT] Backend unreachable sending to {url}, attempt {attempt}/{self.retries}...")
            
            if attempt < self.retries:
                await asyncio.sleep(2 ** (attempt - 1))
            
        logger.error(f"[TRANSPORT] Delivery failed after retries to {url}")
        return False

    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Sends a single telemetry event."""
        success = await self._send_request("/telemetry", event)
        if success:
            machine_id = event.get('machine_id', 'Unknown')
            logger.info(f"[TRANSPORT] Event sent successfully: {machine_id}")
        return success

    async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Sends a batch of telemetry events."""
        if not events:
            return True
            
        payload = {"events": events}
        success = await self._send_request("/telemetry/batch", payload)
        if success:
            logger.info(f"[TRANSPORT] Batch delivered: {len(events)} events")
        return success

    async def health_check(self) -> bool:
        """Checks if backend is available."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"[TRANSPORT] Health check failed: {e}")
            return False

    async def close(self):
        """Closes the async client."""
        await self.client.aclose()
