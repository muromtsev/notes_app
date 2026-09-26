import pytest

from notes_app.db.models.note import Note
from notes_app.db.models.user import User, UserRole
from notes_app.services.note import NoteAccessDeniedError, NoteService


def make_user(id: int = 1, role: UserRole = UserRole.USER) -> User:
    u = User(email=f"u{id}@example.com", hashed_password="x", role=role)
    u.id = id
    return u


def make_note(id: int = 1, owner_id: int = 1) -> Note:
    n = Note(title="title", content="content", owner_id=owner_id)
    n.id = id
    return n


class TestAccessCheck:
    def test_owner_can_access(self):
        NoteService._check_access(make_note(owner_id=1), make_user(id=1))

    def test_admin_can_access_any(self):
        NoteService._check_access(make_note(owner_id=1), make_user(id=99, role=UserRole.ADMIN))

    def test_stranger_cannot_access(self):
        with pytest.raises(NoteAccessDeniedError):
            NoteService._check_access(make_note(owner_id=1), make_user(id=2))
