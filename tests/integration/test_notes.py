import pytest

NOTES_URL = "/api/v1/notes/"
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


async def create_user_and_token(client, email: str) -> str:
    """Регистрирует пользователя и возвращает access_token"""
    await client.post(
        REGISTER_URL,
        json={"email": email, "password": "password123"},
    )
    resp = await client.post(
        LOGIN_URL,
        data={"username": email, "password": "password123"},
    )
    return resp.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_note(client):
    token = await create_user_and_token(client, "n1@example.com")

    resp = await client.post(
        NOTES_URL,
        json={"title": "Hello", "content": "World", "tags": ["work", "urgent"]},
        headers=auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Hello"
    assert data["content"] == "World"
    assert {t["name"] for t in data["tags"]} == {"work", "urgent"}


@pytest.mark.asyncio
async def test_create_note_requires_auth(client):
    resp = await client.post(NOTES_URL, json={"title": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_note_reuses_existing_tags(client):
    """Один и тот же тег не долен дублироваться"""
    token = await create_user_and_token(client, "n2@example.com")

    r1 = await client.post(NOTES_URL, json={"title": "A", "tags": ["shared"]}, headers=auth(token))
    r2 = await client.post(NOTES_URL, json={"title": "B", "tags": ["shared"]}, headers=auth(token))
    assert r1.status_code == 201 and r2.status_code == 201
    tag_id_1 = r1.json()["tags"][0]["id"]
    tag_id_2 = r2.json()["tags"][0]["id"]
    assert tag_id_1 == tag_id_2


@pytest.mark.asyncio
async def test_list_notes_only_own(client):
    """User видит только свои заметки"""
    alice = await create_user_and_token(client, "alice@example.com")
    bob = await create_user_and_token(client, "bob@example.com")

    await client.post(NOTES_URL, json={"title": "Alice note"}, headers=auth(alice))
    await client.post(NOTES_URL, json={"title": "Bob note"}, headers=auth(bob))

    resp = await client.get(NOTES_URL, headers=auth(alice))
    assert resp.status_code == 200
    titles = [n["title"] for n in resp.json()["items"]]
    assert "Alice note" in titles
    assert "Bob note" not in titles


@pytest.mark.asyncio
async def test_get_note_of_another_user_returns_403(client):
    alice = await create_user_and_token(client, "a3@example.com")
    bob = await create_user_and_token(client, "b3@example.com")

    note = (
        await client.post(
            NOTES_URL,
            json={"title": "Private"},
            headers=auth(alice),
        )
    ).json()

    resp = await client.get(
        f"{NOTES_URL}{note['id']}",
        headers=auth(bob),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_note(client):
    token = await create_user_and_token(client, "n4@example.com")
    note = (
        await client.post(NOTES_URL, json={"title": "Old", "content": "c"}, headers=auth(token))
    ).json()

    resp = await client.patch(
        f"{NOTES_URL}{note['id']}",
        json={"title": "New"},
        headers=auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"
    assert resp.json()["content"] == "c"  # не тронуто


@pytest.mark.asyncio
async def test_update_note_tags_empty_clears(client):
    token = await create_user_and_token(client, "n5@example.com")
    note = (
        await client.post(
            NOTES_URL,
            json={"title": "X", "tags": ["a", "b"]},
            headers=auth(token),
        )
    ).json()
    assert len(note["tags"]) == 2

    resp = await client.patch(
        f"{NOTES_URL}{note['id']}",
        json={"tags": []},
        headers=auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


@pytest.mark.asyncio
async def test_delete_note(client):
    token = await create_user_and_token(client, "n6@example.com")
    note = (await client.post(NOTES_URL, json={"title": "To delete"}, headers=auth(token))).json()

    resp = await client.delete(f"{NOTES_URL}{note['id']}", headers=auth(token))
    assert resp.status_code == 204

    resp = await client.get(f"{NOTES_URL}{note['id']}", headers=auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_pagination(client):
    token = await create_user_and_token(client, "n7@example.com")
    for i in range(5):
        await client.post(NOTES_URL, json={"title": f"Note {i}"}, headers=auth(token))

    resp = await client.get(f"{NOTES_URL}?skip=0&limit=2", headers=auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_list_filter_by_tag(client):
    token = await create_user_and_token(client, "n8@example.com")
    await client.post(NOTES_URL, json={"title": "A", "tags": ["work"]}, headers=auth(token))
    await client.post(NOTES_URL, json={"title": "B", "tags": ["personal"]}, headers=auth(token))

    resp = await client.get(f"{NOTES_URL}?tag=work", headers=auth(token))
    titles = [n["title"] for n in resp.json()["items"]]
    assert titles == ["A"]


@pytest.mark.asyncio
async def test_list_search_by_title(client):
    token = await create_user_and_token(client, "n9@example.com")
    await client.post(NOTES_URL, json={"title": "Buy milk"}, headers=auth(token))
    await client.post(NOTES_URL, json={"title": "Call mom"}, headers=auth(token))

    resp = await client.get(f"{NOTES_URL}?search=milk", headers=auth(token))
    titles = [n["title"] for n in resp.json()["items"]]
    assert titles == ["Buy milk"]
