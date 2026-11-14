# Classifieds Pro API Documentation

Base URL for all endpoints is `/api`. Interactive OpenAPI docs are available at `/docs` when the backend is running.

## Authentication

When `ADMIN_API_KEY` is set, every endpoint except `GET /api`, `GET /api/health` and `POST /api/auth/login` requires:

```
Authorization: Bearer <ADMIN_API_KEY>
```

Otherwise the API runs in **open development mode** (no token required) and logs a warning at startup. When `ADMIN_API_KEY` is set, `accounts` responses never include `wanuncios_password` — in fact **no account response ever includes a password**, regardless of mode.

### `POST /api/auth/login` — rate limited (5/minute)

Exchanges the admin key for a token the frontend can store.

- **Request:** `{"username": "admin", "password": "<ADMIN_API_KEY>"}`
- **Response (200):** `{"token": "<ADMIN_API_KEY>", "auth_required": true}`
  - In open development mode: `{"token": "dev-mode-open", "auth_required": false}`
- **Response (401):** invalid credentials. **429** when rate limited.

### `GET /api/health`

- **Response (200):** `{"status": "ok", "mongodb": "connected" | "unavailable"}`

---

## Error semantics

| Code | Meaning |
|---|---|
| 400 | Bad request (e.g. empty PATCH body) |
| 401 | Missing/invalid Bearer token |
| 404 | Referenced entity (or route) not found |
| 409 | Conflict (e.g. publishing with a deactivated account) |
| 422 | Validation error (malformed body) |
| 429 | Rate limit exceeded |
| 503 | Database unavailable (checked per request) |

All create endpoints return **201**; deletes return **204** with an empty body. `PATCH` is idempotent: sending the same values again succeeds (200) — it does not 404 just because nothing changed.

---

## Accounts

Account responses look like:

```json
{
  "id": "a-unique-uuid",
  "email": "user@example.com",
  "is_active": true,
  "captcha_solving_method": "api"
}
```

Passwords are **write-only**: accepted on create/update, stored Fernet-encrypted, never returned.

### `POST /api/accounts/` → 201
- **Body:**
  ```json
  {
    "email": "user@example.com",
    "wanuncios_password": "secure_password123",
    "is_active": true,
    "captcha_solving_method": "api"   // "api" | "manual" | "script"
  }
  ```

### `GET /api/accounts/`
- Query params: `skip` (default 0), `limit` (default 100). Returns a list of account objects.

### `GET /api/accounts/{account_id}` → 200 / 404

### `PATCH /api/accounts/{account_id}`
- **Body (any subset):** `{"email": "...", "wanuncios_password": "...", "is_active": false, "captcha_solving_method": "manual"}`
- Omitting `wanuncios_password` keeps the current password.

### `DELETE /api/accounts/{account_id}` → 204
- **Cascades**: deletes the account's ads, those ads' schedules, and removes the associated scheduler jobs.

---

## Ads

Ad objects:

```json
{
  "id": "a-unique-uuid",
  "account_id": "the-uuid-of-the-account",
  "title": "My Awesome Ad",
  "description": "A great description.",
  "category": "Contactos",
  "subcategory": "Relaciones Ocasionales",
  "province": "Panamá",
  "zone": "San Miguelito",
  "price": 50.0,
  "images": [],
  "created_at": "2026-11-14T12:00:00",
  "last_published_at": null
}
```

- `price` must be a number ≥ 0, `null`, or an empty string (empty string is treated as `null`).
- `zone` empty string is treated as `null`.

### `POST /api/ads/` → 201 / 404 (account not found)
```json
{
  "account_id": "the-uuid-of-the-account",
  "title": "My Awesome Ad",
  "description": "A great description.",
  "category": "Contactos",
  "subcategory": "Relaciones Ocasionales",
  "province": "Panamá",
  "zone": "San Miguelito",
  "price": 50.0,
  "images": []
}
```

### `GET /api/ads/`
- Query params: `skip` (default 0), `limit` (default 100).

### `GET /api/ads/{ad_id}` → 200 / 404

### `PATCH /api/ads/{ad_id}`
- Any subset of ad fields, plus `account_id` (validated — 404 if the target account doesn't exist).

### `DELETE /api/ads/{ad_id}` → 204
- **Cascades**: deletes the ad's schedules and removes their scheduler jobs. `publish_history` rows are kept for audit.

### `POST /api/ads/generate-text` — rate limited (10/minute)
- **Body:** `{"prompt": "A catchy title"}`
- **Response (200):** `{"generated_text": "..."}`
- **Note:** the generator is a placeholder until an LLM provider is wired up (`services/ai_service.py`).

### `POST /api/ads/{ad_id}/publish` — rate limited (20/hour)
- Starts posting the ad in a background task.
- **Response (200):** `{"message": "Ad publishing has been started in the background."}`
- **404** unknown ad, **409** account missing/deactivated. The outcome is recorded: `last_published_at` is set on success and a row is added to `publish_history`.

### `GET /api/ads/{ad_id}/publish-history`
- Query param: `limit` (default 20).
- **Response (200):** list of audit rows (newest first):
  ```json
  [
    {
      "ad_id": "...",
      "account_id": "...",
      "status": "success",
      "detail": "posted",
      "published_at": "2026-11-14T12:00:00"
    }
  ]
  ```
  `status` is `"success"`, `"failed"` or `"skipped"` (account deactivated).

---

## Schedules

Schedule objects:

```json
{
  "id": "a-unique-uuid",
  "ad_id": "the-uuid-of-the-ad",
  "republish_interval_hours": 24,
  "is_active": true,
  "next_republish_at": "2026-11-15T12:00:00"
}
```

`next_republish_at` is recomputed when a schedule is created, its interval changes, or it is re-enabled. Jobs are re-created from the database at application startup, so schedules survive restarts.

### `POST /api/schedules/` → 201 / 404
- **Body:** `{"ad_id": "the-uuid-of-the-ad", "republish_interval_hours": 24}`
- `republish_interval_hours` must be ≥ 1. If the referenced ad (or its account) does not exist, the request fails with 404 **and nothing is persisted**.

### `GET /api/schedules/`
- Query params: `skip` (default 0), `limit` (default 100).

### `GET /api/schedules/{schedule_id}` → 200 / 404

### `PATCH /api/schedules/{schedule_id}`
- **Body (any subset):** `{"republish_interval_hours": 48, "is_active": false}`
- Changing `republish_interval_hours`, or re-enabling a disabled schedule, recomputes `next_republish_at` and re-registers the job.

### `DELETE /api/schedules/{schedule_id}` → 204
- Removes the scheduler job and the schedule row.
