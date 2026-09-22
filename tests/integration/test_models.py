import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from notes_app.db.models import Note, Tag, User, UserRole


@pytest.mark.asyncio
async def test_crate_user(db_session):
    """Пользователь создается и получает id, timestamps"""

    user = User(
        email="user@example.com",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "user@example.com"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_email_unique(db_session):
    """Два пользователя с одним email — IntegrityError."""
    db_session.add(User(email="dup@example.com", hashed_password="x"))
    await db_session.commit()

    db_session.add(User(email="dup@example.com", hashed_password="y"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_note_with_owner(db_session):
    """Заметка привязывается к владельцу."""
    user = User(email="bob@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    note = Note(title="My first note", content="Hello", owner_id=user.id)
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)

    assert note.id is not None
    assert note.owner_id == user.id
    assert note.title == "My first note"


@pytest.mark.asyncio
async def test_note_tags_m2m(db_session):
    """Заметка и теги связаны M2M."""
    user = User(email="carol@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    tag_work = Tag(name="work")
    tag_urgent = Tag(name="urgent")
    note = Note(
        title="Task",
        content="Do it",
        owner_id=user.id,
        tags=[tag_work, tag_urgent],
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)

    result = await db_session.execute(select(Note).where(Note.id == note.id))
    loaded_note = result.scalar_one()

    assert len(loaded_note.tags) == 2
    tag_names = {t.name for t in loaded_note.tags}
    assert tag_names == {"work", "urgent"}


@pytest.mark.asyncio
async def test_delete_user_cascades_notes(db_session):
    """Удаление пользователя удаляет его заметки (CASCADE)."""
    user = User(email="dave@example.com", hashed_password="x")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    note = Note(title="tmp", content="", owner_id=user.id)
    db_session.add(note)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    result = await db_session.execute(select(Note).where(Note.id == note.id))
    assert result.scalar_one_or_none() is None
