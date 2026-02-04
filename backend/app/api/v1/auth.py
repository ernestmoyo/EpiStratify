from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        return await service.login(data.email, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    try:
        return await service.refresh_token(data.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(current_user)
