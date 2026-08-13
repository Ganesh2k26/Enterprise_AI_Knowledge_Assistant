import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    payload = {
        "email": "jane@example.com",
        "full_name": "Jane Doe",
        "password": "SuperSecret123!",
        "organization_name": "Acme Inc",
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == payload["email"]
    assert "access_token" in body
    assert "refresh_token" in body

    r = await client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == payload["email"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    payload = {
        "email": "bob@example.com",
        "full_name": "Bob Smith",
        "password": "CorrectHorse123!",
        "organization_name": "Bob LLC",
    }
    await client.post("/api/v1/auth/register", json=payload)
    r = await client.post("/api/v1/auth/login", json={"email": payload["email"], "password": "wrongpass"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_rejected(client):
    payload = {
        "email": "weak@example.com",
        "full_name": "Weak Password",
        "password": "alllowercase",
        "organization_name": "Weak Inc",
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token_rotates_and_old_one_is_rejected(client):
    payload = {
        "email": "rotate@example.com",
        "full_name": "Rotate User",
        "password": "RotateMe123!",
        "organization_name": "Rotate Inc",
    }
    await client.post("/api/v1/auth/register", json=payload)
    login = await client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    old_refresh = login.json()["refresh_token"]

    first_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first_refresh.status_code == 200

    replay = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401
