from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.services import authenticate_user, create_tokens_for_user, get_current_user_refresh, get_user_by_email, get_current_user
from src.auth.utils import hash_password
from src.auth.exceptions import EmailAlreadyRegistered, ProfileNotFound
from src.database import get_async_session
from src.models.users import User
from src.models.profile import Profile
from src.schemas.token import TokenResponseWithUser
from src.schemas.user import UserCreateRequest, UserLoginRequest, UserResponse, ProfileResponse
from src.models.tokens import RefreshToken
from src.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        max_age=settings.auth_jwt.refresh_token_expires_days * 24 * 60 * 60,
        samesite="none" if settings.is_prod else "lax",
        secure=settings.is_prod
    )



@router.post('/register', response_model=TokenResponseWithUser)
async def register(
    user: UserCreateRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
):
    if await get_user_by_email(user.email, session):
        raise EmailAlreadyRegistered()
    
    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Создаем профиль с пустыми данными
    profile = Profile(
        user_id=new_user.id,
        name="",
        surname="",
    )
    session.add(profile)
    await session.commit()

    access_token, refresh_token = await create_tokens_for_user(new_user, session)
    _set_refresh_cookie(response, refresh_token)
    
    return TokenResponseWithUser(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(new_user)
    )
    
    

@router.post('/login', response_model=TokenResponseWithUser)
async def login(
    response: Response,
    user: UserLoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    user = await authenticate_user(user.email, user.password, session)
    access_token, refresh_token = await create_tokens_for_user(user, session)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponseWithUser(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )



@router.get("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user_refresh),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    token_entry = result.scalars().first()
    if token_entry:
        await session.delete(token_entry)
        await session.commit()

    response.delete_cookie(key="refresh_token")
    return {"detail": "Successfully logged out"}


@router.get("/refresh", response_model=TokenResponseWithUser)
async def refresh_token(
    response: Response,
    current_user: User = Depends(get_current_user_refresh),
    session: AsyncSession = Depends(get_async_session)
):
    access_token, refresh_token = await create_tokens_for_user(current_user, session)
    _set_refresh_cookie(response, refresh_token)
    
    return TokenResponseWithUser(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(current_user)
    )


@router.get('/current_user', response_model=UserResponse)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)
