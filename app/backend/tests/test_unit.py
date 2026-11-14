"""Unit tests for cross-cutting pieces (no ASGI app involved)."""
import types

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.backend.api import deps
from app.backend.services import crypto_service
from app.backend.utils import next_run_after, utcnow


# --- crypto_service -----------------------------------------------------------
def test_crypto_roundtrip():
    secret = "super-secret-pw-123"
    token = crypto_service.encrypt_text(secret)
    assert token != secret
    assert crypto_service.decrypt_text(token) == secret


def test_crypto_decrypt_falls_back_to_plaintext():
    # Legacy plaintext rows (pre-encryption) must still be readable.
    assert crypto_service.decrypt_text("legacy-plaintext-pw") == "legacy-plaintext-pw"


# --- auth dependency ----------------------------------------------------------
async def test_require_admin_open_when_unset(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    assert await deps.require_admin(None) is True


async def test_require_admin_rejects_missing_or_wrong_token(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "correct-key")
    with pytest.raises(HTTPException) as exc:
        await deps.require_admin(None)
    assert exc.value.status_code == 401

    wrong = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-key")
    with pytest.raises(HTTPException) as exc:
        await deps.require_admin(wrong)
    assert exc.value.status_code == 401


async def test_require_admin_accepts_correct_token(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "correct-key")
    good = HTTPAuthorizationCredentials(scheme="Bearer", credentials="correct-key")
    assert await deps.require_admin(good) is True


# --- database dependency ------------------------------------------------------
async def test_get_database_503_when_unavailable():
    fake_request = types.SimpleNamespace(app=types.SimpleNamespace(mongodb=None))
    with pytest.raises(HTTPException) as exc:
        await deps.get_database(fake_request)
    assert exc.value.status_code == 503


# --- utils --------------------------------------------------------------------
def test_next_run_after_is_in_future():
    assert next_run_after(24) > utcnow()


# --- scheduler rehydration -----------------------------------------------------
async def test_rehydrate_jobs_recreates_jobs_for_active_schedules(monkeypatch, mock_db):
    from app.backend.models.account import AccountCreate
    from app.backend.models.ad import AdCreate
    from app.backend.models.schedule import ScheduleCreate
    from app.backend.services import account_service, ad_service, schedule_service, scheduler_service

    account = await account_service.create_account(
        mock_db, AccountCreate(email="rehydrate@example.com", wanuncios_password="pw")
    )
    ad = await ad_service.create_ad(
        mock_db,
        AdCreate(
            account_id=account.id, title="t", description="d",
            category="Contactos", subcategory="Relaciones Ocasionales", province="Panamá",
        ),
    )
    schedule = await schedule_service.create_schedule(
        mock_db, ScheduleCreate(ad_id=ad.id, republish_interval_hours=12)
    )

    added = []

    monkeypatch.setattr(scheduler_service, "_db", mock_db)
    fake = type("FakeScheduler", (), {"running": True})()
    monkeypatch.setattr(scheduler_service, "scheduler", fake)
    monkeypatch.setattr(fake, "add_job", lambda *args, **kwargs: added.append((args, kwargs)), raising=False)

    count = await scheduler_service.rehydrate_jobs()
    assert count == 1
    args, kwargs = added[0]
    assert args[0] is scheduler_service.run_ad_publish
    assert args[1] == "interval"
    assert kwargs["id"] == f"post_ad_{schedule.id}"
    assert kwargs["args"] == [ad.id, schedule.id]
    assert kwargs["replace_existing"] is True
    assert kwargs["coalesce"] is True
