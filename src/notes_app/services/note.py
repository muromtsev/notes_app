from sqlalchemy.ext.asyncio import AsyncSession

from notes_app.core.exceptions import AppError
from notes_app.db.models.note import Note
from notes_app.db.models.user import User, UserRole
from notes_app.repositories.note import NoteRepository
from notes_app.schemas.note import NoteCreate, NoteListParams, NoteUpdate


class NoteNotFoundError(AppError):
    status_code = 404
    code = "note_not_found"


class NoteAccessDeniedError(AppError):
    status_code = 403
    code = "note_access_denied"


class NoteService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.notes = NoteRepository(session)

    @staticmethod
    def _check_access(note: Note, user: User) -> None:
        """Owner or Admin иначе 403"""
        if user.role == UserRole.ADMIN:
            return
        if note.owner_id != user.id:
            raise NoteAccessDeniedError("You don't have access to this note")

    async def create(self, payload: NoteCreate, user: User) -> Note:
        tags = await self._resolve_tags(payload.tags)
        note = await self.notes.create(
            title=payload.title, content=payload.content, owner_id=user.id, tags=tags
        )

        await self.session.commit()
        loaded = await self.notes.get_by_id(note.id)
        assert loaded is not None
        return loaded

    async def get(self, note_id: int, user: User) -> Note:
        note = await self.notes.get_by_id(note_id)
        if note is None:
            raise NoteNotFoundError(f"Note {note_id} not found")
        self._check_access(note, user)
        return note

    async def list_notes(
        self,
        user: User,
        params: NoteListParams,
    ) -> tuple[list[Note], int]:
        """Admin видит все заметки, user - только свои"""
        owner_id = None if user.role == UserRole.ADMIN else user.id
        return await self.notes.list_paginated(
            owner_id=owner_id,
            skip=params.skip,
            limit=params.limit,
            search=params.search,
            tag=params.tag,
            order_by=params.order_by,
        )

    async def update(
        self,
        note_id: int,
        payload: NoteUpdate,
        user: User,
    ) -> Note:
        note = await self.get(note_id, user)
        fields = payload.model_dump(exclude_unset=True)
        tag_names = fields.pop("tags", None)

        if fields:
            await self.notes.update(note, **fields)

        if tag_names is not None:
            tags = await self._resolve_tags(tag_names)
            note.tags = tags
            await self.session.flush()

        await self.session.commit()
        loaded = await self.notes.get_by_id(note.id)
        assert loaded is not None
        return loaded

    async def delete(self, note_id: int, user: User) -> None:
        note = await self.get(note_id, user)
        await self.notes.delete(note)
        await self.session.commit()

    async def _resolve_tags(self, names: list[str]) -> list:
        if not names:
            return []

        cleaned = list({name.strip() for name in names if name.strip()})
        if not cleaned:
            return []

        existing = await self.notes.get_tags_by_names(cleaned)
        existing_names = {t.name for t in existing}

        to_create = [name for name in names if name not in existing_names]
        created = await self.notes.create_tags(to_create) if to_create else []
        return existing + created
