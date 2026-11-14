import uuid


def unique_email(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4()}@example.com"


async def create_account(client, email=None, password="password123"):
    response = await client.post(
        "/api/accounts/",
        json={"email": email or unique_email(), "wanuncios_password": password},
    )
    assert response.status_code == 201
    return response.json()


async def create_ad(client, account_id, **overrides):
    ad = {
        "account_id": account_id,
        "title": "Test Ad",
        "description": "This is a test description.",
        "category": "Contactos",
        "subcategory": "Relaciones Ocasionales",
        "province": "Panamá",
    }
    ad.update(overrides)
    response = await client.post("/api/ads/", json=ad)
    assert response.status_code == 201
    return response.json()


async def test_read_root(client):
    response = await client.get("/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Classifieds Pro API"}


async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_accounts_crud(client):
    email = unique_email("test-acc")

    # --- CREATE ---
    response = await client.post("/api/accounts/", json={"email": email, "wanuncios_password": "password123"})
    assert response.status_code == 201
    created_account = response.json()
    # Passwords must never be returned by the API.
    assert "wanuncios_password" not in created_account
    account_id = created_account["id"]

    # --- READ (one) ---
    response = await client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["email"] == email
    assert "wanuncios_password" not in response.json()

    # --- READ (list) ---
    response = await client.get("/api/accounts/")
    assert response.status_code == 200
    assert all("wanuncios_password" not in a for a in response.json())

    # --- PATCH with no effective change: must succeed (matched_count semantics) ---
    response = await client.patch(f"/api/accounts/{account_id}", json={"email": email})
    assert response.status_code == 200
    assert response.json()["email"] == email

    # --- PATCH with a real change ---
    response = await client.patch(f"/api/accounts/{account_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # --- DELETE ---
    response = await client.delete(f"/api/accounts/{account_id}")
    assert response.status_code == 204
    assert response.content == b""

    # --- READ after DELETE ---
    response = await client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 404


async def test_account_password_stored_encrypted(client, mock_db):
    account = await create_account(client, password="super-secret-pw")
    stored = await mock_db.accounts.find_one({"id": account["id"]})
    assert stored["wanuncios_password"] != "super-secret-pw"
    assert stored["wanuncios_password"].startswith("gAAAAA")


async def test_ads_crud(client):
    account = await create_account(client, email=unique_email("test-ad"))

    # --- CREATE (with blank price string — must not 422) ---
    ad = {
        "account_id": account["id"],
        "title": "Test Ad",
        "description": "This is a test description.",
        "category": "Contactos",
        "subcategory": "Relaciones Ocasionales",
        "province": "Panamá",
        "price": "",
        "zone": "",
    }
    response = await client.post("/api/ads/", json=ad)
    assert response.status_code == 201
    created_ad = response.json()
    assert created_ad["price"] is None
    assert created_ad["zone"] is None
    ad_id = created_ad["id"]

    # --- READ ---
    response = await client.get(f"/api/ads/{ad_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Ad"

    # --- PATCH with no effective change ---
    response = await client.patch(f"/api/ads/{ad_id}", json={"title": "Test Ad"})
    assert response.status_code == 200

    # --- DELETE ---
    response = await client.delete(f"/api/ads/{ad_id}")
    assert response.status_code == 204
    response = await client.get(f"/api/ads/{ad_id}")
    assert response.status_code == 404


async def test_create_ad_rejects_unknown_account(client):
    ad = {
        "account_id": "no-such-account",
        "title": "Test Ad",
        "description": "desc",
        "category": "Contactos",
        "subcategory": "Relaciones Ocasionales",
        "province": "Panamá",
    }
    response = await client.post("/api/ads/", json=ad)
    assert response.status_code == 404


async def test_schedules_crud(client, mock_db):
    # --- Creating a schedule for a nonexistent ad must 404 and NOT persist a row ---
    response = await client.post("/api/schedules/", json={"ad_id": "no-such-ad", "republish_interval_hours": 24})
    assert response.status_code == 404
    rows = [doc async for doc in mock_db.schedules.find({"ad_id": "no-such-ad"})]
    assert rows == []

    # --- Valid flow ---
    account = await create_account(client, email=unique_email("test-sched"))
    ad = await create_ad(client, account["id"], title="Sched Test Ad", description="d")

    response = await client.post("/api/schedules/", json={"ad_id": ad["id"], "republish_interval_hours": 12})
    assert response.status_code == 201
    schedule = response.json()
    schedule_id = schedule["id"]
    assert "next_republish_at" in schedule

    response = await client.get(f"/api/schedules/{schedule_id}")
    assert response.status_code == 200
    assert response.json()["republish_interval_hours"] == 12

    # --- PATCH interval recomputes next_republish_at ---
    response = await client.patch(f"/api/schedules/{schedule_id}", json={"republish_interval_hours": 48})
    assert response.status_code == 200
    assert response.json()["next_republish_at"] is not None

    # --- PATCH toggle off ---
    response = await client.patch(f"/api/schedules/{schedule_id}", json={"is_active": False})
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    response = await client.delete(f"/api/schedules/{schedule_id}")
    assert response.status_code == 204


async def test_delete_ad_cascades_schedules(client, mock_db):
    account = await create_account(client, email=unique_email("test-cascade"))
    ad = await create_ad(client, account["id"])
    response = await client.post("/api/schedules/", json={"ad_id": ad["id"], "republish_interval_hours": 24})
    assert response.status_code == 201

    response = await client.delete(f"/api/ads/{ad['id']}")
    assert response.status_code == 204

    rows = [doc async for doc in mock_db.schedules.find({"ad_id": ad["id"]})]
    assert rows == []


async def test_delete_account_cascades_ads_and_schedules(client, mock_db):
    account = await create_account(client, email=unique_email("test-cascade-acc"))
    ad = await create_ad(client, account["id"])
    response = await client.post("/api/schedules/", json={"ad_id": ad["id"], "republish_interval_hours": 24})
    assert response.status_code == 201

    response = await client.delete(f"/api/accounts/{account['id']}")
    assert response.status_code == 204

    assert [doc async for doc in mock_db.ads.find({"account_id": account["id"]})] == []
    assert [doc async for doc in mock_db.schedules.find({"ad_id": ad["id"]})] == []


async def test_publish_endpoint(client):
    account = await create_account(client, email=unique_email("test-pub"))
    ad = await create_ad(client, account["id"], title="Publish Test")

    response = await client.post(f"/api/ads/{ad['id']}/publish")
    assert response.status_code == 200
    assert "message" in response.json()


async def test_publish_history_endpoint(client):
    account = await create_account(client, email=unique_email("test-hist"))
    ad = await create_ad(client, account["id"])

    response = await client.get(f"/api/ads/{ad['id']}/publish-history")
    assert response.status_code == 200
    assert response.json() == []


async def test_publish_rejects_deactivated_account(client):
    account = await create_account(client, email=unique_email("test-deact"))
    ad = await create_ad(client, account["id"])
    await client.patch(f"/api/accounts/{account['id']}", json={"is_active": False})

    response = await client.post(f"/api/ads/{ad['id']}/publish")
    assert response.status_code == 409


async def test_generate_text(client):
    response = await client.post("/api/ads/generate-text", json={"prompt": "A catchy title"})
    assert response.status_code == 200
    assert "generated_text" in response.json()
