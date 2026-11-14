# Classifieds Pro

Classifieds Pro is a full-stack application designed to automate the management and posting of classified ads to wanuncios.com. It provides a web dashboard to manage accounts, generate ad content with AI, and schedule automatic ad posting and republishing.

## Key Features

- **Account Management:** Store multiple `wanuncios.com` user accounts. Passwords are stored **Fernet-encrypted** at rest and never returned by the API.
- **Ad Management:** Full CRUD for ad templates, including AI-assisted description generation (placeholder until a provider is wired up).
- **Scheduling System:** Automatic republishing of ads at user-defined intervals. Jobs are re-created from the database at startup, so republishing survives restarts.
- **Web Automation:** A Playwright-based service that automates logging in and posting ads.
- **Admin Authentication:** All `/api` routes (except the root, health and login endpoints) require a Bearer token when `ADMIN_API_KEY` is set.
- **Modern UI:** React + shadcn/ui dashboard with toasts, a login screen and a real dashboard page.

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **Database:** MongoDB (via `motor`)
- **Web Automation:** Playwright
- **Scheduling:** APScheduler (jobs re-hydrated from MongoDB at startup)
- **Encryption:** `cryptography` (Fernet) for credential encryption
- **Rate limiting:** `slowapi`

### Frontend
- **Framework:** React (via `create-react-app` / `react-scripts` 5)
- **UI Library:** `shadcn/ui` (Radix primitives)
- **Styling:** Tailwind CSS
- **API Communication:** Axios (shared instance with auth interceptors)

## Project Structure

Monorepo located in `/app`:

- `/app/backend`: The FastAPI application.
  - `/api`: Endpoint routers (`accounts`, `ads`, `schedules`, `deps`).
  - `/models`: Pydantic data models.
  - `/services`: Business logic — AI, automation, CAPTCHA, crypto, scheduler.
  - `/tests`: Integration tests (mocked DB via `mongomock-motor`) + unit tests.
- `/app/frontend`: The React application.
  - `/src/components`: Reusable components (`ui/` = shadcn components).
  - `/src/pages`: Page components.
  - `/src/services`: API clients (`api.js` is the shared axios instance).

## Setup and Installation

### Backend

1. **Navigate to the project root:**
   ```bash
   cd /path/to/ClassifiedsPro
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r app/backend/requirements.txt   # add -r app/backend/requirements-dev.txt for tests
   ```

3. **Create the environment file:**
   ```bash
   cp app/backend/.env.example app/backend/.env
   ```
   Then edit `app/backend/.env`. Key settings:
   | Variable | Purpose |
   |---|---|
   | `MONGO_URL` / `DB_NAME` | MongoDB connection |
   | `MONGO_SERVER_SELECTION_TIMEOUT_MS` | How long to wait for Mongo at startup (default 2500) |
   | `CORS_ORIGINS` | Comma-separated dashboard origins (no `*` with credentials) |
   | `ADMIN_API_KEY` | **Required in production.** Bearer token for the API and the dashboard password |
   | `CREDENTIAL_ENCRYPTION_KEY` | **Required in production.** Fernet key for encrypting stored wanuncios passwords |
   | `TWOCAPTCHA_API_KEY` | 2captcha key used by the automation service |
   | `UNIVERSAL_KEY` | LLM key for AI ad generation (not yet wired up) |
   | `RATE_LIMIT_ENABLED` | `true`/`false` (disable in tests) |

   Generate keys with:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"              # ADMIN_API_KEY
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # CREDENTIAL_ENCRYPTION_KEY
   ```

### Frontend

1. **Navigate to the frontend directory:**
   ```bash
   cd app/frontend
   ```
2. **Install NPM dependencies:**
   ```bash
   npm ci
   ```
3. *(Optional)* point the app at a non-local backend:
   ```bash
   echo "REACT_APP_API_URL=http://your-backend:8001/api" > .env.local
   ```

## Running

### Everything (Docker Compose)

```bash
cp app/backend/.env.example app/backend/.env   # set ADMIN_API_KEY etc.
docker compose up --build
```
Dashboard at `http://localhost:3000`, API at `http://localhost:8001`, MongoDB included.

### Backend (local)

```bash
cd /path/to/ClassifiedsPro
python -m uvicorn app.backend.main:app --reload --port 8001
```
The API is available at `http://localhost:8001` (docs at `http://localhost:8001/docs`).

### Frontend (local)

```bash
cd app/frontend
npm start
```
The dashboard is available at `http://localhost:3000`. Sign in with the `ADMIN_API_KEY` from your `.env` (any username; the key is the password).

## Testing

From the **project root**:
```bash
python -m pytest
```
This runs 21 integration/unit tests. The integration tests mock MongoDB (`mongomock-motor`) and the scheduler/automation services; no MongoDB or browser is required. Config lives in `pytest.ini`.

Frontend:
```bash
cd app/frontend
CI=true npx react-scripts test --watchAll=false
npm run build
```

CI (`.github/workflows/ci.yml`) runs both suites on every push/PR.

## Security Notes

- **Rotate the `UNIVERSAL_KEY` and `TWOCAPTCHA_API_KEY` that were committed in `app/backend/.env` before adopting this branch.** They remain in the git history of `main`; treat them as compromised. (`.gitignore` now excludes `.env`; the file is untracked as of this branch.)
- The API is **open development mode** when `ADMIN_API_KEY` is unset. Set it anywhere the API is reachable beyond your machine.
- Stored wanuncios passwords are encrypted with `CREDENTIAL_ENCRYPTION_KEY`. Credentials saved **before** encryption was introduced are still readable (decrypt falls back to plaintext) and are re-encrypted the next time the account is saved. If `CREDENTIAL_ENCRYPTION_KEY` is unset, an ephemeral key is generated at startup and stored credentials become unreadable after restart.
- Passwords (plaintext or decrypted) are never returned by the API; `AccountOut` has no password field.
- `/api/auth/login` and the publish/generate endpoints are rate-limited.
- Automating wanuncios.com — including solving its CAPTCHAs — may violate its Terms of Service and can get the underlying accounts banned. Review and accept that risk yourself, and double-check the legal status of any adult-content categories you intend to post.

## Known Limitations

- **Automation selectors are unverified.** The URLs and CSS selectors in `automation_service.py` are placeholders and have never been validated against the live site. Site inspection and test runs (headed mode, `captcha_solving_method: "manual"`) are required before relying on it.
- **CAPTCHA solving** requires a funded 2captcha account; the `script` method is not implemented; `manual` requires a non-headless browser and a human.
- **AI text generation is a placeholder** — `emergentintegrations` is not publicly installable, so `/ads/generate-text` returns placeholder text until a provider is wired in (see `services/ai_service.py`).
- **Single-admin auth.** There is one shared credential, not per-user accounts.
- **No unique constraint on `accounts.email`** — duplicates are allowed at the database level.
- Docker images are provided but were not built/tested in every environment; verify `docker compose up --build` on your machine (it also downloads the Playwright Chromium browser on first build).

## How Republishing Works

`POST /schedules/` stores the schedule in MongoDB and registers an APScheduler interval job (in memory). At startup, `scheduler_service.rehydrate_jobs()` re-creates a job for every active schedule — jobs carry only `ad_id`/`schedule_id`, and account/ad state is read fresh from the database on every run. Deleting an ad, account or schedule cascades to its jobs; deactivating an account stops its ads from publishing (the job skips and logs). Each publish attempt is recorded in the `publish_history` collection and surfaced via `GET /api/ads/{ad_id}/publish-history`.
