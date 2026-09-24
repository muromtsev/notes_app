from sqlalchemy.ext.asyncio import AsyncSession

from notes_app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
)
from notes_app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token_or_none,
    hash_password,
    verify_password,
)
from notes_app.db.models.user import User
from notes_app.repositories.user import UserRepository
from notes_app.schemas.token import Token


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register(self, email: str, password: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyExistsError(f"Email {email} already registered")

        user = await self.users.create(
            email=email,
            hashed_password=hash_password(password),
        )
        await self.session.commit()
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InvalidCredentialsError("User is inactive")
        return user

    def issue_tokens(self, user: User) -> Token:
        return Token(
            access_token=create_access_token(user.id, extra_claims={"role": user.role}),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> Token:
        payload = decode_token_or_none(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid refresh token")

        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError):
            raise InvalidTokenError("Invalid refresh token") from None

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        if not user.is_active:
            raise InvalidCredentialsError("User is inactive")

        return self.issue_tokens(user)

    async def get_user_from_access_token(self, token: str) -> User:
        payload = decode_token_or_none(token)
        if payload is None or payload.get("type") != "access":
            raise InvalidTokenError("Invalid access token")

        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError):
            raise InvalidTokenError("Invalid access token") from None

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        return user
