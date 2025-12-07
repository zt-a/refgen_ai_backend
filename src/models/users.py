from src.db_base import Base
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.essay import Essay
from src.models.tokens import RefreshToken
from src.models.profile import Profile
from src.config import settings

class User(Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(30))
    
    email: Mapped[str] = mapped_column(String(100), unique=True)
    
    balance: Mapped[int] = mapped_column(Integer, default=settings.default_balance)

    hashed_password: Mapped[str] = mapped_column(String(128))
    
    is_active: Mapped[bool] = mapped_column(default=True)
    
    is_superuser: Mapped[bool] = mapped_column(default=False)
    
    is_verified: Mapped[bool] = mapped_column(default=False)
    
    profile: Mapped["Profile"] = relationship("Profile", uselist=False, back_populates="user")
    
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    essays: Mapped[list["Essay"]] = relationship(
        "Essay",
        back_populates="user",
        cascade="",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r})"

    
