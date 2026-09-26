from fastapi import APIRouter

from notes_app.api.v1 import auth, notes

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(notes.router)
