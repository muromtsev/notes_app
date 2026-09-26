from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from notes_app.db.models.note import Note, Tag


class NoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, note_id: int) -> Note | None:
        """Загрузка заметки с тегом"""
        result = await self.session.execute(
            select(Note).options(selectinload(Note.tags)).where(Note.id == note_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        *,
        owner_id: int | None,
        skip: int,
        limit: int,
        search: str | None = None,
        tag: str | None = None,
        order_by: str = "-created_at",
    ) -> tuple[list[Note], int]:
        """Возвращает (страница заметок, общее количество)"""
        base = select(Note).options(selectinload(Note.tags))

        if owner_id is not None:
            base = base.where(Note.owner_id == owner_id)

        if search:
            base = base.where(Note.title.ilike(f"%{search}%"))

        if tag:
            base = base.join(Note.tags).where(Tag.name == tag)

        if order_by.startswith("-"):
            column_name = order_by[1:]
            direction = "desc"
        else:
            column_name = order_by
            direction = "asc"

        allowed_columns = {"created_at", "updated_at", "title", "id"}

        if column_name not in allowed_columns:
            column_name = "created_at"
            direction = "desc"

        column = getattr(Note, column_name)
        base = base.order_by(column.desc() if direction == "desc" else column.asc())

        count_query = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        result = await self.session.execute(base.offset(skip).limit(limit))
        notes = list(result.scalars().unique().all())

        return notes, total

    async def create(
        self,
        *,
        title: str,
        content: str,
        owner_id: int,
        tags: list[Tag] | None = None,
    ) -> Note:
        note = Note(
            title=title,
            content=content,
            owner_id=owner_id,
            tags=tags or [],
        )
        self.session.add(note)
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def update(self, note: Note, **fields) -> Note:
        for key, value in fields.items():
            setattr(note, key, value)
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def delete(self, note: Note) -> Note:
        await self.session.delete(note)
        await self.session.flush()

    async def get_tags_by_names(self, names: list[str]) -> list[Tag]:
        if not names:
            return []
        result = await self.session.execute(select(Tag).where(Tag.name.in_(names)))
        return list(result.scalars().all())

    async def create_tags(self, names: list[str]) -> list[Tag]:
        tags = [Tag(name=name) for name in names]
        self.session.add_all(tags)
        await self.session.flush()
        return tags
