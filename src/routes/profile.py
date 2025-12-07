from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import ProfileNotFound
from src.database import get_async_session
from src.auth.services import get_current_user
from src.models.users import User
from src.models.profile import Profile
from src.schemas.profile import (
    ProfileCreateRequest,
    ProfileResponse
)

router = APIRouter(prefix="/profile", tags=["Profile"])


# =========================================================
# GET /profile/me — получить профиль текущего пользователя
# =========================================================
@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    if not current_user.profile:
        raise ProfileNotFound()

    return current_user.profile


# =========================================================
# POST /profile — создать профиль (если нет)
# =========================================================
@router.post("/", response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.profile:
        raise HTTPException(status_code=400, detail="Profile already exists")

    new_profile = Profile(
        user_id=current_user.id,
        **profile_data.model_dump()
    )

    session.add(new_profile)
    await session.commit()
    await session.refresh(new_profile)

    return new_profile


# =========================================================
# PUT /profile — обновить профиль
# =========================================================
@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    profile = current_user.profile

    if not profile:
        raise ProfileNotFound()

    update_fields = profile_data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(profile, key, value)

    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    return profile


# =========================================================
# DELETE /profile — удалить свой профиль
# =========================================================
@router.delete("/", status_code=204)
async def delete_profile(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    profile = current_user.profile

    if not profile:
        raise ProfileNotFound()

    await session.delete(profile)
    await session.commit()

    return
