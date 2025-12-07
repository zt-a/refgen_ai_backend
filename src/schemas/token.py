
from pydantic import BaseModel
from src.schemas.user import UserResponse

# ===========================
# Auth / Tokens Schemas
# ===========================

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponseWithUser(TokenResponse):
    user: UserResponse