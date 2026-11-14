"""Shared helpers for the Classifieds Pro backend."""
from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    """Naive UTC datetime (MongoDB stores naive datetimes by convention)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def next_run_after(hours: int) -> datetime:
    return utcnow() + timedelta(hours=hours)
