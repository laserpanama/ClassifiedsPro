"""Shared FastAPI dependencies: database access and admin authentication."""
import hmac
import logging
import os

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


async def get_database(request: Request) -> AsyncIOMotorDatabase:
    """Returns the connected database, or a clean 503 when it is unavailable."""
    db = getattr(request.app, "mongodb", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database is unavailable. Try again later.")
    return db


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> bool:
    """
    Enforces the admin API key when ADMIN_API_KEY is configured.

    With ADMIN_API_KEY unset the API runs in "open development mode" and every
    request is allowed (a loud warning is logged at startup). Set the variable
    for anything reachable beyond your machine.
    """
    expected = os.getenv("ADMIN_API_KEY", "").strip()
    if not expected:
        return True
    token = credentials.credentials if credentials else ""
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
