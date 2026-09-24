import jose.jwt  # type: ignore[import-untyped]

from notes_app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decode_token_or_none,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    plain = "super-secret-123"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_hash_is_salted():
    """Одинаковые пароли дают разные хеши"""
    pass1 = hash_password("same-password")
    pass2 = hash_password("same-password")

    assert pass1 != pass2


def test_create_and_decode_access_token():
    token = create_access_token(subject=42, extra_claims={"role": "admin"})
    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_create_refresh_token_has_refresh_type():
    token = create_refresh_token(subject=1)
    payload = decode_token(token)

    assert payload["type"] == "refresh"


def test_decode_invalid_token_returns_none():
    assert decode_token_or_none("not-a-jwt") is None


def test_decode_token_with_wrong_signature_returns_none():
    """Токен подписанный другим ключом не пройдет валидацию"""
    foreign = jose.jwt.encode({"sub": "1"}, "wrong-key", algorithm="HS256")

    assert decode_token_or_none(foreign) is None


def test_tokens_are_unique_thanks_to_jti():
    """Даже одинаковые claims дают разные токены благодаря jti."""
    t1 = create_access_token(subject=1)
    t2 = create_access_token(subject=1)
    assert t1 != t2

    p1 = decode_token(t1)
    p2 = decode_token(t2)
    assert p1["jti"] != p2["jti"]
    assert p1["sub"] == p2["sub"]
    assert p1["type"] == p2["type"]

