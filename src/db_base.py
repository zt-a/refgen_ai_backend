from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr, mapped_column, Mapped

class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() 

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

