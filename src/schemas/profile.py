
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime


# ===========================
# Profile Schemas
# ===========================

class ProfileBase(BaseModel):
    name: str
    surname: str
    patronymic: Optional[str] = None
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    group: Optional[str] = None
    city: Optional[str] = None
    phone_number: Optional[str] = None
    # phone_number_verified: Optional[bool] = False
    # avatar_url: Optional[str] = None

class ProfileCreateRequest(ProfileBase):
    pass  # для создания/обновления профиля

class ProfileResponse(ProfileBase):
    user_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
