"""
Athena Client service for the AutoForge backend.
Handles querying AWS Athena, polling for completion, parsing column results,
and gracefully handling errors.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List
import boto3

from backend.core.config import get_settings
from backend.core.logger import get_logger

logger = get_logger("AthenaClient")
settings = get_settings()


class AthenaClient:
    """
    Client wrapper for executing queries asynchronously against Amazon Athena.
    """

    def __init__(self) -> None:
        self.region = settings.AWS_REGION
        self.database = settings.ATHENA_DATABASE
        self.workgroup = settings.ATHENA_WORKGROUP
        self.client = boto3.client("athena", region_name=self.region)
        logger.info(
            f"[ATHENA] Initialized client region={self.region} "
            f"database={self.database} workgroup={self.workgroup}"
        )

    async def execute_query(self, query_string: str) -> List[Dict[str, Any]]:
        """
        Execute an Athena query asynchronously, poll for completion, and return results.
        """
        logger.info(f"[ATHENA] Executing query: {query_string.strip()[:100]}...")
        try:
            loop = asyncio.get_running_loop()
            
            # Start query execution in executor to avoid blocking the event loop
            response = await loop.run_in_executor(
                None,
                lambda: self.client.start_query_execution(
                    QueryString=query_string,
                    QueryExecutionContext={"Database": self.database},
                    WorkGroup=self.workgroup,
                ),
            )
            execution_id = response["QueryExecutionId"]
            logger.info(f"[ATHENA] Query started execution_id={execution_id}")

            # Poll for completion with exponential backoff
            delay = 0.1
            while True:
                status_resp = await loop.run_in_executor(
                    None,
                    lambda: self.client.get_query_execution(QueryExecutionId=execution_id),
                )
                status = status_resp["QueryExecution"]["Status"]["State"]
                
                if status == "SUCCEEDED":
                    logger.info(f"[ATHENA] Query {execution_id} succeeded")
                    break
                elif status in ["FAILED", "CANCELLED"]:
                    reason = status_resp["QueryExecution"]["Status"].get(
                        "StateChangeReason", "Unknown reason"
                    )
                    raise RuntimeError(f"Athena query {execution_id} {status}: {reason}")
                
                await asyncio.sleep(delay)
                # Cap the backoff at 1.0 second
                delay = min(delay * 2, 1.0)

            # Retrieve results
            results = await loop.run_in_executor(
                None,
                lambda: self.client.get_query_results(QueryExecutionId=execution_id),
            )
            return self._parse_results(results)

        except Exception as e:
            logger.error(f"[ATHENA] Query execution failed: {e}")
            raise

    def _parse_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Athena's column-oriented row structure into standard dictionary format.
        """
        rows = results.get("ResultSet", {}).get("Rows", [])
        if not rows:
            return []

        # The first row contains the headers
        headers = [col.get("VarCharValue", "") for col in rows[0].get("Data", [])]

        parsed = []
        for r in rows[1:]:
            row_data = {}
            for i, col in enumerate(r.get("Data", [])):
                val = col.get("VarCharValue", None)
                key = headers[i] if i < len(headers) else f"col_{i}"
                row_data[key] = val
            parsed.append(row_data)

        return parsed
