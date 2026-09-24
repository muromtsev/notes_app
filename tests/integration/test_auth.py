import pytest


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
ME_URL = "/api/v1/auth/me"


async def register(client, email="user@example.com", password="password123"):
    return await client.post(
        REGISTER_URL,
        json={"email": email, "password": password},
    )


async def login(client, email="user@example.com", password="password123"):
    return await client.post(
        LOGIN_URL,
        data={"username": email, "password": password},
    )


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await register(client)
    resp = await register(client)
    assert resp.status_code == 409
    assert resp.json()["code"] == "email_already_exists"


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post(
        REGISTER_URL,
        json={"email": "x@example.com", "password": "short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await register(client)
    resp = await login(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await register(client)
    resp = await login(client, password="wrong-password")
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await login(client, email="nobody@example.com")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client):
    await register(client)
    tokens = (await login(client)).json()

    resp = await client.get(
        ME_URL,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_me_without_token(client):
    resp = await client.get(ME_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_refresh_token_fails(client):
    """Refresh-токен не должен пускать в /me."""
    await register(client)
    tokens = (await login(client)).json()

    resp = await client.get(
        ME_URL,
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client):
    await register(client)
    tokens = (await login(client)).json()

    resp = await client.post(
        REFRESH_URL,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    me_resp = await client.get(
        ME_URL,
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client):
    """Access-токен не должен работать как refresh."""
    await register(client)
    tokens = (await login(client)).json()

    resp = await client.post(
        REFRESH_URL,
        json={"refresh_token": tokens["access_token"]},
    )
    assert resp.status_code == 401

