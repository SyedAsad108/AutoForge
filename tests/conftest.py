"""
pytest conftest — ensures lambda handler modules don't collide in sys.modules
when both test files are run in the same session.

Each lambda is loaded under a unique alias so that `handler` from
lambda/validator/ and `handler` from lambda/glue_trigger/ coexist.
"""
import sys
import importlib
import importlib.util
import os


def _load_lambda(alias: str, path: str):
    """Load a lambda handler module under a unique sys.modules alias."""
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# Pre-load both handlers under unique names before any test collects
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DATA_LAKE_BUCKET",  "test-data-lake")
os.environ.setdefault("QUARANTINE_BUCKET", "test-quarantine")
os.environ.setdefault("GLUE_JOB_NAME",     "autoforge-etl-raw-to-curated")

_load_lambda(
    "lambda_validator_handler",
    os.path.join(_ROOT, "lambda", "validator", "handler.py"),
)
_load_lambda(
    "lambda_glue_trigger_handler",
    os.path.join(_ROOT, "lambda", "glue_trigger", "handler.py"),
)
