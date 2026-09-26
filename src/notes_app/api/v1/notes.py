from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from notes_app.api.deps import CurrentUser, DbSession
from notes_app.schemas.note import (
    NoteCreate,
    NoteListParams,
    NoteListResponse,
    NoteRead,
    NoteUpdate,
)
from notes_app.services.note import NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


def get_note_service(session: DbSession) -> NoteService:
    return NoteService(session)


NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]


@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    user: CurrentUser,
    service: NoteServiceDep,
):
    return await service.create(payload, user)


@router.get("/", response_model=NoteListResponse)
async def list_notes(
    user: CurrentUser,
    service: NoteServiceDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=255)] = None,
    tag: Annotated[str | None, Query(max_length=50)] = None,
    order_by: Annotated[str, Query(max_length=50)] = "-created_at",
):
    params = NoteListParams(
        skip=skip,
        limit=limit,
        search=search,
        tag=tag,
        order_by=order_by,
    )
    notes, total = await service.list_notes(user, params)
    return {
        "items": [NoteRead.model_validate(n) for n in notes],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: int,
    user: CurrentUser,
    service: NoteServiceDep,
):
    return await service.get(note_id, user)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    user: CurrentUser,
    service: NoteServiceDep,
):
    return await service.update(note_id, payload, user)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    user: CurrentUser,
    service: NoteServiceDep,
):
    await service.delete(note_id, user)
