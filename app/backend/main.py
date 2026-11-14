import sys
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import hmac
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.backend.api import accounts, ads, schedules
from app.backend.api.deps import require_admin
from app.backend.rate_limit import limiter
from app.backend.services import scheduler_service

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MONGO_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "2500"))


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup...")

    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")

    if not mongo_url or not db_name:
        logger.error("MONGO_URL and DB_NAME must be set in the environment — running without a database.")
        app.mongodb_client = None
        app.mongodb = None
    else:
        app.mongodb_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=MONGO_TIMEOUT_MS)
        app.mongodb = app.mongodb_client[db_name]
        try:
            await app.mongodb_client.admin.command('ping')
            logger.info("MongoDB connection successful.")
        except Exception as e:
            logger.error(f"MongoDB connection failed (continuing without DB): {e}")
            app.mongodb_client = None
            app.mongodb = None

    if not os.getenv("ADMIN_API_KEY"):
        logger.warning(
            "ADMIN_API_KEY is not set — the API is in OPEN development mode (anyone can call it). "
            "Set ADMIN_API_KEY in app/backend/.env before deploying."
        )

    await scheduler_service.initialize_scheduler(app.mongodb)

    yield

    # Shutdown
    logger.info("Application shutdown...")
    await scheduler_service.shutdown_scheduler()
    if app.mongodb_client:
        app.mongodb_client.close()
        logger.info("Disconnected from MongoDB.")


# Create the main app
app = FastAPI(title="Classifieds Pro API", lifespan=lifespan)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add API routers (all behind admin auth when ADMIN_API_KEY is set)
app.include_router(accounts.router, prefix="/api", dependencies=[Depends(require_admin)])
app.include_router(ads.router, prefix="/api", dependencies=[Depends(require_admin)])
app.include_router(schedules.router, prefix="/api", dependencies=[Depends(require_admin)])

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic root endpoint (public)
@app.get("/api")
async def root():
    return {"message": "Welcome to Classifieds Pro API"}


# Health check (public) — reports database reachability for monitoring
@app.get("/api/health")
async def health(request: Request):
    db = getattr(request.app, "mongodb", None)
    return {"status": "ok", "mongodb": "connected" if db is not None else "unavailable"}


class LoginRequest(BaseModel):
    username: str = "admin"
    password: str


# Dashboard login (public, rate-limited).
# The admin API key doubles as the dashboard password: callers exchange it for
# the same token, which they then send as a Bearer token on API requests.
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def auth_login(request: Request, body: LoginRequest):
    expected = os.getenv("ADMIN_API_KEY", "").strip()
    if not expected:
        # Open development mode — auth is disabled, no real token exists.
        return {"token": "dev-mode-open", "auth_required": False}
    if hmac.compare_digest(body.password, expected):
        return {"token": expected, "auth_required": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")
