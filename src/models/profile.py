
from datetime import datetime
from src.db_base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Profile(Base):
    __tablename__ = 'profiles'
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True)
    
    name: Mapped[str] = mapped_column(String(50))
    
    surname: Mapped[str] = mapped_column(String(50))
    
    patronymic: Mapped[str] = mapped_column(String(50), nullable=True)
    
    phone_number: Mapped[str] = mapped_column(String(15), nullable=True)     
    
    phone_number_verified: Mapped[bool] = mapped_column(default=False)
    
    university: Mapped[str] = mapped_column(String(100), nullable=True)
    
    faculty: Mapped[str] = mapped_column(String(100), nullable=True)
    
    course: Mapped[int] = mapped_column(Integer, nullable=True)
    
    group: Mapped[str] = mapped_column(String(100), nullable=True)
    
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # avatar_url: Mapped[str] = mapped_column(String(200), nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="profile") # type: ignore
    

    def __repr__(self) -> str:
        return f"Profile(id={self.id!r}, user_id={self.user_id!r}, name={self.name!r}, surname={self.surname!r}, avatar_url={self.avatar_url!r})"
