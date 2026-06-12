"""
AutoForge Glue ETL Trigger — Phase 7
Lambda Function: EventBridge → Glue startJobRun

Called by EventBridge (either on S3 Object Created events in raw/
or on the scheduled 5-minute rule). Guards against concurrent runs:
if a Glue job is already RUNNING/STARTING, the invocation is skipped.

Environment variables:
  GLUE_JOB_NAME  — name of the Glue ETL job to trigger
"""

import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue = boto3.client("glue")
GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]

# States that mean a job is actively running and should not be double-triggered
_ACTIVE_STATES = {"RUNNING", "STARTING", "STOPPING"}


def _is_job_active() -> bool:
    """Return True if the most recent job run is in an active state."""
    try:
        resp = glue.get_job_runs(JobName=GLUE_JOB_NAME, MaxResults=5)
        for run in resp.get("JobRuns", []):
            if run["JobRunState"] in _ACTIVE_STATES:
                logger.info(
                    f"[TRIGGER] Glue job already {run['JobRunState']} "
                    f"(run_id={run['JobRunId']}). Skipping."
                )
                return True
    except ClientError as exc:
        logger.warning(f"[TRIGGER] Could not check job runs: {exc}")
    return False


def handler(event, context):
    """
    EventBridge invocation handler.

    Logs the triggering event source, checks for active runs,
    and starts a new Glue job run if safe to do so.
    """
    source = event.get("source", "unknown")
    detail_type = event.get("detail-type", "unknown")
    logger.info(f"[TRIGGER] Received event  source={source}  detail-type={detail_type}")

    if _is_job_active():
        return {
            "status": "skipped",
            "reason": "job_already_active",
            "job": GLUE_JOB_NAME,
        }

    try:
        resp = glue.start_job_run(JobName=GLUE_JOB_NAME)
        job_run_id = resp["JobRunId"]
        logger.info(f"[TRIGGER] Started Glue job run  job={GLUE_JOB_NAME}  run_id={job_run_id}")
        return {
            "status": "started",
            "jobRunId": job_run_id,
            "job": GLUE_JOB_NAME,
        }
    except ClientError as exc:
        logger.error(f"[TRIGGER] Failed to start Glue job: {exc}")
        raise
