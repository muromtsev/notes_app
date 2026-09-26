import pytest

REGISTER_URL = "/api/v1/auth/register"
NOTES_URL = "/api/v1/notes/"


@pytest.mark.asyncio
async def test_request_id_in_response_headers(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers


@pytest.mark.asyncio
async def test_custom_request_id_is_preserved(client):
    resp = await client.get(
        "/health",
        headers={"X-Request-ID": "my-trace-id"},
    )
    assert resp.headers["x-request-id"] == "my-trace-id"


@pytest.mark.asyncio
async def test_validation_error_format(client):
    resp = await client.post(
        REGISTER_URL,
        json={"email": "not-an-email", "password": "x"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validation_error"
    assert body["detail"] == "Validation error"
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) >= 1
    # Проверим, что есть ошибка по email и по password
    fields = {e["field"] for e in body["errors"]}
    assert any("email" in f for f in fields)
    assert any("password" in f for f in fields)


@pytest.mark.asyncio
async def test_unauthorized_format(client):
    """401 от get_current_user — в едином формате."""
    resp = await client.get(NOTES_URL)
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "http_401"
    assert "detail" in body


@pytest.mark.asyncio
async def test_not_found_format(client):
    """404 от роутера — в едином формате."""
    resp = await client.get("/api/v1/no-such-route")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "http_404"
