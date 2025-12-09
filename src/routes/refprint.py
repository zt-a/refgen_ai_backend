from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from io import BytesIO
from docx import Document
import os 

from src.refprint.frontpage import FrontPage
from src.auth.services import get_current_user
from src.database import get_async_session
from src.models.essay import Essay
from src.models.users import User
from src.refprint.refprint import RefPrint
from src.config import settings




router = APIRouter(prefix="/refprint", tags=["RefPrint"])

SAVE_DIR = settings.refprint.save_dir
os.makedirs(SAVE_DIR, exist_ok=True)

@router.get("/{essay_id}")
async def refprint(
    essay_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Получаем эссе с главами
    result = await session.execute(
        select(Essay)
        .options(selectinload(Essay.chapters))
        .options(selectinload(Essay.essay_metadata))
        .where(Essay.id == essay_id, Essay.user_id == current_user.id)
    )
    essay = result.scalars().first()
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")
    print(essay)
    # Путь к файлу
    safe_filename = f"{essay.id}_{essay.topic}.docx"
    file_path = os.path.join(SAVE_DIR, safe_filename)

    # Если файл уже сохранён, отдаем его
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=safe_filename
        )

    # Создаём документ и RefPrint
    doc = Document()
    
    front = FrontPage(
        university=essay.essay_metadata.university.capitalize(),
        faculty=essay.essay_metadata.faculty.capitalize(),
        subject=essay.essay_metadata.subject.capitalize(),
        topic=essay.topic.capitalize(),
        course=essay.essay_metadata.course,
        performed_by=essay.essay_metadata.performed_by.capitalize(),
        checked_by=essay.essay_metadata.checked_by.capitalize(),
        group=essay.essay_metadata.group.capitalize(),
        city=essay.essay_metadata.city.capitalize(),
        year=essay.essay_metadata.year,
        doc=doc
    )
    
    doc = front.write()
    
    ref = RefPrint(doc)
    
    ref.add_footer()
    
    chapter_title = ''
    
    # Добавляем план из chapter title
    for chapter in essay.chapters:
        chapter_title += f'<li>{chapter.title}\n</li>'
        
    ref.ref_add(
        f"""
<document>
<content>
<h2>Содержание</h2>
<ul>
    <li>Введение\n</li>
    {chapter_title}
    <li>Заключение\n</li>
    <li>Использованные Источники\n</li>
</ul>
<br>
</content>
</document>
        """
    )
    
    br = "<document><content><br></content></document>"
    ref.ref_add(
        f"""
<document>
<content>
<h2>Введение</h2>
</content>
</document>
        """
    )
    # Добавляем introduction если есть
    if essay.introduction:
        ref.ref_add(essay.introduction)
        ref.ref_add(br)
        
        
        
    # Добавляем главы
    for chapter in essay.chapters:
        if chapter.content:
            ref.ref_add(chapter.content)
            ref.ref_add(br)

    ref.ref_add(
        f"""
<document>
<content>
<h2>Заключение</h2>
</content>
</document>
        """
    )
    
    # Добавляем conclusion и references, если есть
    if essay.conclusion:
        ref.ref_add(essay.conclusion)
        ref.ref_add(br)
        
    ref.ref_add(
        f"""
<document>
<content>
<h2>Использованные Источники</h2>
</content>
</document>
        """
    )
    if essay.references:
        ref.ref_add(essay.references)

    # Генерируем документ
    doc = ref.ref_print()
    
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = 'Times New Roman'

    # Сохраняем на диск
    doc.save(file_path)

    # Отдаём пользователю
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_filename
    )
