"""
Unit tests for the Glue Trigger Lambda.
Tests cover: job-already-running guard, successful start, and error handling.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Use the alias pre-loaded by conftest.py to avoid module collision
handler = sys.modules["lambda_glue_trigger_handler"]


def _make_event(source="aws.events", detail_type="Scheduled Event"):
    return {"source": source, "detail-type": detail_type, "detail": {}}


class TestGlueTrigger(unittest.TestCase):

    def test_starts_job_when_idle(self):
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {"JobRuns": []}
        mock_glue.start_job_run.return_value = {"JobRunId": "jr-001"}

        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(_make_event(), None)

        self.assertEqual(result["status"], "started")
        self.assertEqual(result["jobRunId"], "jr-001")
        mock_glue.start_job_run.assert_called_once_with(
            JobName="autoforge-etl-raw-to-curated"
        )

    def test_skips_when_job_running(self):
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {
            "JobRuns": [{"JobRunState": "RUNNING", "JobRunId": "jr-000"}]
        }

        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(_make_event(), None)

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "job_already_active")
        mock_glue.start_job_run.assert_not_called()

    def test_skips_when_job_starting(self):
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {
            "JobRuns": [{"JobRunState": "STARTING", "JobRunId": "jr-002"}]
        }
        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(_make_event(), None)
        self.assertEqual(result["status"], "skipped")

    def test_proceeds_when_last_run_succeeded(self):
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {
            "JobRuns": [{"JobRunState": "SUCCEEDED", "JobRunId": "jr-003"}]
        }
        mock_glue.start_job_run.return_value = {"JobRunId": "jr-004"}

        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(_make_event(), None)
        self.assertEqual(result["status"], "started")

    def test_proceeds_when_last_run_failed(self):
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {
            "JobRuns": [{"JobRunState": "FAILED", "JobRunId": "jr-005"}]
        }
        mock_glue.start_job_run.return_value = {"JobRunId": "jr-006"}

        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(_make_event(), None)
        self.assertEqual(result["status"], "started")

    def test_raises_on_glue_client_error(self):
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {"JobRuns": []}
        mock_glue.start_job_run.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}},
            "StartJobRun",
        )
        with patch.object(handler, "glue", mock_glue):
            with self.assertRaises(ClientError):
                handler.handler(_make_event(), None)

    def test_get_job_runs_failure_does_not_block_start(self):
        """If we can't check job status, we should still try to start."""
        mock_glue = MagicMock()
        mock_glue.get_job_runs.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}},
            "GetJobRuns",
        )
        mock_glue.start_job_run.return_value = {"JobRunId": "jr-007"}

        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(_make_event(), None)
        self.assertEqual(result["status"], "started")

    def test_s3_event_source_logged(self):
        """Verify S3 event source is handled without errors."""
        mock_glue = MagicMock()
        mock_glue.get_job_runs.return_value = {"JobRuns": []}
        mock_glue.start_job_run.return_value = {"JobRunId": "jr-008"}
        s3_event = {
            "source": "aws.s3",
            "detail-type": "Object Created",
            "detail": {
                "bucket": {"name": "autoforge-data-lake"},
                "object": {"key": "raw/machine_type=cnc/test.json"},
            },
        }
        with patch.object(handler, "glue", mock_glue):
            result = handler.handler(s3_event, None)
        self.assertEqual(result["status"], "started")


if __name__ == "__main__":
    unittest.main()
