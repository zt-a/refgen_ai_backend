from src.db_base import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timedelta, timezone
from src.config import settings

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)  # уникальный токен на пользователя
    token: Mapped[str] = mapped_column(String(2048), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(
            days=settings.auth_jwt.refresh_token_expires_days or 30
        )
    )



    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")  # type: ignore

    @classmethod
    def create(cls, user_id: int, token: str, expires_in_days: int = settings.auth_jwt.refresh_token_expires_days or 30):
        return cls(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        )
