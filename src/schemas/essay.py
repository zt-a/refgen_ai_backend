from pydantic import BaseModel
from enum import Enum
from src.models.essay import EnumLanguage



class EnumLanguage(str, Enum):
    RU = "ru"
    EN = "en"
    KG = "kg" 
    
    
class RefRequest(BaseModel):
    topic: str
    checked_by: str
    subject: str
    page_count: int = 20
    chapters_count: int = 6
    language: str = EnumLanguage.RU
    
    
class UpdateChapterRequest(BaseModel):
    chapter_id: int
    title: str
