import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from notes_app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]

def hash_password(password: str) -> str:
    """Хэширует пароль через bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Проверят пароль против хэша"""
    return pwd_context.verify(plain, hashed)

def _create_token(
        subject: str | int,
        token_type: TokenType,
        expires_delta: timedelta,
        extra_claims: dict[str, Any] | None = None,
) -> str:
    """Содает JWT-токен с заданным типом и сроком"""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def create_access_token(
        subject: str | int,
        extra_claims: dict[str, Any] | None = None,
) -> str:
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims=extra_claims
    )

def create_refresh_token(subject: str | int) -> str:
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )

def decode_token(token: str) -> dict[str, Any]:
    """Декодирует и валидирует JWT. Бросает JWTError при проблемах"""
    return jwt.decode(
        token, settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

def decode_token_or_none(token: str) -> dict[str, Any] | None:
    """Мягкий вариант - возвращает None вместо исключения"""
    try:
        return decode_token(token)
    except JWTError:
        return None

