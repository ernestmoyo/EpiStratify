import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import RefreshToken, User
from app.schemas.user import TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserCreate) -> UserResponse:
        # Check for existing user
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("A user with this email already exists")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            organization=data.organization,
        )
        self.db.add(user)
        await self.db.flush()

        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("User account is inactive")

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Store refresh token
        token_record = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(token_record)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        payload = verify_token(refresh_token_str)
        if payload is None or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        # Check token in database
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token_str,
                RefreshToken.revoked == False,
            )
        )
        token_record = result.scalar_one_or_none()

        if token_record is None:
            raise ValueError("Refresh token not found or revoked")

        if token_record.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired")

        # Revoke old token
        token_record.revoked = True

        # Create new tokens
        user_id = payload["sub"]
        new_access_token = create_access_token({"sub": user_id})
        new_refresh_token = create_refresh_token({"sub": user_id})

        new_token_record = RefreshToken(
            token=new_refresh_token,
            user_id=uuid.UUID(user_id),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(new_token_record)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
