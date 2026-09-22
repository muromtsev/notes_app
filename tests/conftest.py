from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from notes_app.core.config import settings
from notes_app.core.logging import setup_logging
from notes_app.db.base import Base

setup_logging("WARNING")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_engine():
    """Движок для тестовой БД. Один на всю сессию, в одном loop."""
    engine = create_async_engine(settings.test_database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Сессия с откатом транзакции после теста. Работает в session-loop."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
