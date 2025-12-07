from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, String, Integer, ForeignKey, DateTime, Text
from src.db_base import Base



class EnumStatus(str, Enum):
    PENDING = "PENDING"
    PLAN_GENERATED = "PLAN_GENERATED"
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    COMPLETED = "COMPLETED"
    FAILURE = "FAILURE"
    ERROR = "ERROR"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class EnumLanguage(str, Enum):
    RU = "ru"
    EN = "en"
    KG = 'kg'
    

class Essay(Base):
    __tablename__ = 'essays'
    
    topic: Mapped[str] = mapped_column(String(255), nullable=False)  # обязательное
    task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=20, nullable=False)  # теперь необязательное
    status: Mapped[str] = mapped_column(String(255), nullable=False, default=EnumStatus.PENDING)
    language: Mapped[str] = mapped_column(String(255), nullable=False, default=EnumLanguage.RU)

    chapter_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    introduction: Mapped[str] = mapped_column(Text, nullable=True)
    introduction_chars_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    conclusion: Mapped[str] = mapped_column(Text, nullable=True)
    conclusion_chars_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    references: Mapped[str] = mapped_column(Text, nullable=True)
    references_chars_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    essay_metadata: Mapped['EssayMetadata'] = relationship(
        back_populates='essay',
        cascade='all, delete-orphan',
        uselist=False
    )
    
    chapters: Mapped[list['Chapter']] = relationship(
        back_populates='essay',
        cascade='all, delete-orphan',
        uselist=True
    )
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)
    user: Mapped['User'] = relationship(back_populates='essays') # type: ignore


class Chapter(Base):
    __tablename__ = 'chapters'
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # теперь необязательное
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    chars: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)

    essay_id: Mapped[int] = mapped_column(ForeignKey('essays.id'))
    essay: Mapped['Essay'] = relationship(back_populates='chapters')


class EssayMetadata(Base):
    __tablename__ = 'essay_metadata'
    
    university: Mapped[str] = mapped_column(String(255), nullable=True)
    faculty: Mapped[str] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    course: Mapped[int] = mapped_column(Integer, nullable=True)
    
    performed_by: Mapped[str] = mapped_column(String(255), nullable=True)
    checked_by: Mapped[str] = mapped_column(String(255), nullable=True)
    group: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True, default=datetime.now().year)

    essay_id: Mapped[int] = mapped_column(ForeignKey('essays.id'))
    essay: Mapped['Essay'] = relationship(back_populates='essay_metadata')
