from sqlalchemy.orm import selectinload

from datetime import datetime, timezone
from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from src.database import get_async_session
from src.models.tokens import RefreshToken
from src.models.users import User
from src.auth.utils import create_access_token, create_refresh_token, decode_jwt, verify_password
from src.auth.exceptions import (
    InvalidCredentials, InactiveUser, MissingAccessToken, InvalidAccessToken,
    InvalidTokenPayload, MissingRefreshToken, InvalidRefreshToken, UserNotFound
)


auth_scheme = HTTPBearer(auto_error=False)


async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(user_id: int, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def authenticate_user(email: str, password: str, session: AsyncSession) -> User:
    user = await get_user_by_email(email, session)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveUser()
    return user


async def create_tokens_for_user(user: User, session: AsyncSession):
    jwt_data = {
        "sub": str(user.id),  # Преобразуем в строку для PyJWT
        "email": user.email,
        "username": user.username,
        "balance": user.balance,
    }
    access_token = create_access_token(data=jwt_data)
    refresh_token = create_refresh_token(data=jwt_data)
    
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    session.add(RefreshToken.create(user_id=user.id, token=refresh_token))
    await session.commit()
    
    return access_token, refresh_token


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    if not credentials:
        raise MissingAccessToken()

    payload = decode_jwt(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise InvalidTokenPayload()

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise InvalidTokenPayload()

    result = await session.execute(
        select(User).where(User.id == user_id).options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFound()

    return user


async def get_current_user_refresh(
    refresh_token: str | None = Cookie(None),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    if not refresh_token:
        raise MissingRefreshToken()

    payload = decode_jwt(refresh_token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise InvalidTokenPayload()

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise InvalidTokenPayload()

    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    )
    
    if not result.scalar_one_or_none():
        raise InvalidRefreshToken()

    result = await session.execute(
        select(User).where(User.id == user_id).options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFound()

    return user


async def get_current_user_profile(
    user: User = Depends(get_current_user),
):
    return user.profile
