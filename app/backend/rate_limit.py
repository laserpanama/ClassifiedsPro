"""Shared rate limiter (slowapi). Set RATE_LIMIT_ENABLED=false to disable (e.g. tests)."""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() in ("1", "true", "yes")

limiter = Limiter(key_func=get_remote_address, enabled=RATE_LIMIT_ENABLED)
