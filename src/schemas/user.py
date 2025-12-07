from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime

from src.schemas.profile import ProfileResponse
from src.config import settings


# ===========================
# User Schemas
# ===========================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    balance: int = Field(default=settings.default_balance, ge=0)

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    # profile: Optional[ProfileResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserProfileResponse(BaseModel):
    id: int
    profile: Optional[ProfileResponse]

    model_config = ConfigDict(from_attributes=True)
