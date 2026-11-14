import os

# Test environment MUST be set before importing the app.
# Fail fast on the (nonexistent) MongoDB ping so startup doesn't block.
os.environ["MONGO_SERVER_SELECTION_TIMEOUT_MS"] = "300"
# Disable rate limiting for tests.
os.environ["RATE_LIMIT_ENABLED"] = "false"
# Throwaway Fernet key used only by the test-suite — not a real secret.
os.environ["CREDENTIAL_ENCRYPTION_KEY"] = "4xFdFS8Skzgleace3W_Uux2AetZ_qhs5BNovgcor4hE="
# Auth open for the API test-suite; auth itself is covered in test_unit.py.
os.environ.pop("ADMIN_API_KEY", None)

import pytest
import httpx
from asgi_lifespan import LifespanManager
from motor.motor_asyncio import AsyncIOMotorDatabase
import mongomock_motor

from app.backend.main import app as main_app
from app.backend.api import deps


# --- Mocking Services ---
@pytest.fixture(scope="session", autouse=True)
def mock_services(session_mocker):
    """Mocks scheduler/automation for the entire test session."""
    session_mocker.patch("app.backend.services.scheduler_service.initialize_scheduler", return_value=None)
    session_mocker.patch("app.backend.services.scheduler_service.shutdown_scheduler", return_value=None)
    session_mocker.patch("app.backend.services.scheduler_service.schedule_ad_posting_job", return_value=True)
    session_mocker.patch("app.backend.services.scheduler_service.remove_schedule", return_value=True)
    session_mocker.patch("app.backend.services.scheduler_service.sync_next_run", return_value=None)
    session_mocker.patch("app.backend.services.automation_service.post_ad_to_wanuncios", return_value=True)


# --- Mocking the Database ---
@pytest.fixture(scope="session")
def mock_db():
    """Provides a mock database for the test session."""
    return mongomock_motor.AsyncMongoMockClient().get_database("test_db")


@pytest.fixture(scope="session", autouse=True)
def override_db_dependency(mock_db):
    """Applies the database dependency override for the entire session."""
    async def override_get_database() -> AsyncIOMotorDatabase:
        return mock_db

    main_app.dependency_overrides[deps.get_database] = override_get_database
    yield
    main_app.dependency_overrides = {}


@pytest.fixture(scope="session")
async def client():
    """Async HTTP client; LifespanManager handles startup and shutdown."""
    async with LifespanManager(main_app):
        transport = httpx.ASGITransport(app=main_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture(scope="function", autouse=True)
async def clear_collections(mock_db):
    """Clears all data from the mock database after each test."""
    yield
    for collection in await mock_db.list_collection_names():
        await mock_db[collection].delete_many({})
