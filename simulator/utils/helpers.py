import datetime
import random

def get_current_timestamp() -> str:
    """Returns the current timestamp in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def random_fluctuation(value: float, variance_pct: float) -> float:
    """Applies a random fluctuation to a value based on a percentage variance."""
    variance = value * variance_pct
    return value + random.uniform(-variance, variance)
