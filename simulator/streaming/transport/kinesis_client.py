"""
Kinesis Data Streams Transport Client — Phase 4.3

Replaces the FastAPI HTTP transport with a direct boto3 producer
that publishes telemetry events to an AWS Kinesis Data Stream.

Design decisions:
- Partition key = machine_id  → preserves per-machine ordering
- Batch via put_records()     → up to 500 records / 5 MB per call
- Async-safe via run_in_executor → boto3 is synchronous; we offload
  the blocking call to a thread-pool so the asyncio event loop is
  never blocked.
- Failed records are logged and counted; they are NOT retried here
  because Kinesis returns partial failures inline.
"""

import asyncio
import json
from typing import Any, Dict, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from simulator.utils.logger import setup_logger
from simulator.utils.constants import (
    KINESIS_STREAM_NAME,
    KINESIS_REGION,
    KINESIS_MAX_BATCH_SIZE,
    KINESIS_RETRY_ATTEMPTS,
)

logger = setup_logger("KinesisClient")

# Kinesis hard limits
_KINESIS_MAX_RECORDS_PER_CALL = 500
_KINESIS_MAX_BATCH_BYTES = 5 * 1024 * 1024  # 5 MB


class KinesisTransportClient:
    """
    Async-safe boto3 producer for AWS Kinesis Data Streams.

    Usage::

        client = KinesisTransportClient()
        await client.send_batch(events)
        await client.close()
    """

    def __init__(self):
        self._stream_name = KINESIS_STREAM_NAME
        self._region = KINESIS_REGION
        self._max_batch = min(KINESIS_MAX_BATCH_SIZE, _KINESIS_MAX_RECORDS_PER_CALL)
        self._retries = KINESIS_RETRY_ATTEMPTS

        self._kinesis = boto3.client("kinesis", region_name=self._region)

        # Metrics
        self._records_sent: int = 0
        self._records_failed: int = 0
        self._batches_sent: int = 0

        logger.info(
            f"[KINESIS] Transport initialised  "
            f"stream={self._stream_name}  region={self._region}  "
            f"max_batch={self._max_batch}"
        )

    # ------------------------------------------------------------------
    # Public API (mirrors TelemetryAPIClient for drop-in compatibility)
    # ------------------------------------------------------------------

    async def send_event(self, event: Dict[str, Any]) -> bool:
        """Send a single telemetry event to Kinesis."""
        return await self.send_batch([event])

    async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
        """
        Send a batch of telemetry events to Kinesis.

        Splits large batches to honour the 500-record / 5 MB limits,
        then offloads the blocking boto3 call to the thread pool.
        """
        if not events:
            return True

        all_ok = True
        # Chunk into safe sizes
        for chunk in self._chunk_events(events):
            ok = await self._put_records_with_retry(chunk)
            if not ok:
                all_ok = False

        return all_ok

    async def health_check(self) -> bool:
        """Verify the stream is ACTIVE."""
        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: self._kinesis.describe_stream_summary(
                    StreamName=self._stream_name
                ),
            )
            status = (
                resp.get("StreamDescriptionSummary", {})
                .get("StreamStatus", "UNKNOWN")
            )
            is_active = status == "ACTIVE"
            logger.info(f"[KINESIS] Health check — stream status: {status}")
            return is_active
        except Exception as exc:
            logger.error(f"[KINESIS] Health check failed: {exc}")
            return False

    async def close(self):
        """No persistent connection to close for boto3; log final stats."""
        logger.info(
            f"[KINESIS] Transport closing  "
            f"records_sent={self._records_sent}  "
            f"records_failed={self._records_failed}  "
            f"batches_sent={self._batches_sent}"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _chunk_events(
        self, events: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Split events into chunks that respect both the 500-record limit
        and the approximate 5 MB payload limit.
        """
        chunks: List[List[Dict[str, Any]]] = []
        current_chunk: List[Dict[str, Any]] = []
        current_bytes = 0

        for event in events:
            data_bytes = json.dumps(event).encode("utf-8")
            record_bytes = len(data_bytes) + len(
                event.get("machine_id", "unknown").encode("utf-8")
            )

            if (
                len(current_chunk) >= self._max_batch
                or current_bytes + record_bytes > _KINESIS_MAX_BATCH_BYTES
            ):
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = []
                current_bytes = 0

            current_chunk.append(event)
            current_bytes += record_bytes

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _build_kinesis_records(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert event dicts into the format expected by put_records()."""
        records = []
        for event in events:
            # Strip internal queue metadata before sending to Kinesis
            clean_event = {k: v for k, v in event.items() if k != "_enqueue_epoch"}
            records.append(
                {
                    "Data": json.dumps(clean_event).encode("utf-8"),
                    "PartitionKey": str(event.get("machine_id", "unknown")),
                }
            )
        return records

    async def _put_records_with_retry(
        self, events: List[Dict[str, Any]]
    ) -> bool:
        """
        Call put_records() with exponential back-off on throttling errors.
        Returns True if all records were accepted.
        """
        records = self._build_kinesis_records(events)
        loop = asyncio.get_running_loop()

        for attempt in range(1, self._retries + 1):
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda r=records: self._kinesis.put_records(
                        StreamName=self._stream_name,
                        Records=r,
                    ),
                )

                failed_count = response.get("FailedRecordCount", 0)
                self._batches_sent += 1
                self._records_sent += len(records) - failed_count
                self._records_failed += failed_count

                if failed_count == 0:
                    logger.info(
                        f"[KINESIS] Batch delivered  "
                        f"records={len(records)}  attempt={attempt}"
                    )
                    return True
                else:
                    logger.warning(
                        f"[KINESIS] Partial failure  "
                        f"failed={failed_count}/{len(records)}  attempt={attempt}"
                    )
                    # Kinesis partial failures are usually due to throttling;
                    # retry the whole chunk after back-off (simpler and safe
                    # because records are idempotent telemetry snapshots).
                    if attempt < self._retries:
                        await asyncio.sleep(2 ** (attempt - 1))
                    continue

            except (BotoCoreError, ClientError) as exc:
                logger.error(
                    f"[KINESIS] put_records error on attempt {attempt}/{self._retries}: {exc}"
                )
                if attempt < self._retries:
                    await asyncio.sleep(2 ** (attempt - 1))

        logger.error(
            f"[KINESIS] Delivery failed after {self._retries} attempts for "
            f"{len(records)} records"
        )
        self._records_failed += len(records)
        return False
