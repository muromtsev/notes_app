from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from notes_app.schemas.tag import TagRead


class NoteBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = ""


class NoteCreate(NoteBase):
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    tags: list[str] | None = None


class NoteRead(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    tags: list[TagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class NoteListParams(BaseModel):
    """Параметры для GET /notes"""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    search: str | None = None
    tag: str | None = None
    order_by: str = Field(default="-created_at")


class NoteListResponse(BaseModel):
    items: list[NoteRead]
    total: int
    skip: int
    limit: int
