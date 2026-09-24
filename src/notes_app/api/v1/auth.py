from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from notes_app.api.deps import CurrentUser, get_auth_service
from notes_app.schemas.token import RefreshRequest, Token
from notes_app.schemas.user import UserCreate, UserRead
from notes_app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, service: AuthServiceDep):
    return await service.register(email=payload.email, password=payload.password)

@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                service: AuthServiceDep,
):
    user = await service.authenticate(
        email=form_data.username,
        password=form_data.password,
    )
    return service.issue_tokens(user)

@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, service: AuthServiceDep):
    return await service.refresh(payload.refresh_token)

@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser):
    return user

