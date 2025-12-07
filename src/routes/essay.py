from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.services import get_current_user
from src.models.profile import Profile
from src.models.users import User
from src.models.essay import EnumLanguage, Essay, EssayMetadata, EnumStatus, Chapter
from src.database import get_async_session
from src.schemas.essay import RefRequest, UpdateChapterRequest
from src.refagent.agents.plan_agent import PlanAgent
from src.refagent.utils import chars_to_page, distribute_pages_with_priority, parse_plan
from src.celery_app import celery_app
from src.tasks.essay import generate_essay
from src.config import settings





router = APIRouter(prefix="/essays", tags=["Essay"])

# ========================================================= 
@router.post("/plan/generate")
async def generate_plan(
    ref_request: RefRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Получаем профиль пользователя
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile: Profile | None = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Профиль пользователя не найден. Пожалуйста, заполните профиль."
        )

    # Проверяем необходимые поля профиля
    required_fields = {
        "name": profile.name,
        "surname": profile.surname,
        "university": profile.university,
        "faculty": profile.faculty,
        "course": profile.course,
        "group": profile.group,
        "city": profile.city
    }
    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Профиль пользователя не заполнен. Отсутствуют поля: {', '.join(missing_fields)}"
        )

    # 1. Генерируем план
    plan_agent = PlanAgent()
    plan = plan_agent.generate_plan(
        topic=ref_request.topic,
        chapters_count=ref_request.chapters_count,
        language=ref_request.language
    )
    plan_list = parse_plan(plan)
    if not plan_list:
        requested_chapters = ref_request.chapters_count or 1
        plan_list = [f"Глава {idx}" for idx in range(1, requested_chapters + 1)]
    chapters_count = len(plan_list) or 1

    # Определяем страницы для введения, заключения, глав
    if ref_request.page_count <= 20:
        pages = 1
    elif ref_request.page_count <= 40:
        pages = 2
    else:
        pages = 3

    try:
        pages_priority = distribute_pages_with_priority(
            total_pages=ref_request.page_count,
            intro_pages=pages,
            conclusion_pages=pages,
            references_pages=1,
            number_of_chapters=chapters_count
        )

        introduction_chars = chars_to_page(
            pages_priority.get("introduction", pages)
        )
        conclusion_chars = chars_to_page(
            pages_priority.get("conclusion", pages)
        )
        references_chars = chars_to_page(
            pages_priority.get("references", 1)
        )

        chapter_pages = pages_priority.get("chapters", [])
        if len(chapter_pages) != chapters_count:
            raise ValueError("Количество распределённых страниц не совпадает с количеством глав.")
        chapters_chars = [chars_to_page(chapter_page) for chapter_page in chapter_pages]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации плана: {str(e)}"
        )

    # 2. Создаём Essay
    essay = Essay(
        topic=ref_request.topic or "Без темы",
        page_count=ref_request.page_count or 20,
        language=ref_request.language or EnumLanguage.RU,
        chapter_count=chapters_count,
        introduction_chars_count=introduction_chars.get("chars", 1000),
        conclusion_chars_count=conclusion_chars.get("chars", 1000),
        references_chars_count=references_chars.get("chars", 500),
        status=EnumStatus.PLAN_GENERATED,
        user_id=current_user.id
    )
    session.add(essay)
    await session.flush()  # получаем essay.id

    # 3. Создаём metadata (1 к 1)
    essay_metadata = EssayMetadata(
        essay_id=essay.id,
        university=profile.university or "Не указано",
        faculty=profile.faculty or "Не указано",
        subject=ref_request.subject or "Не указано",
        course=profile.course or 1,
        performed_by=f"{profile.surname} {profile.name}",
        checked_by=ref_request.checked_by or "Не указано",
        group=profile.group or "Не указано",
        city=profile.city or "Не указано"
    )
    session.add(essay_metadata)

    # 4. Создаём главы (1 ко многим)
    default_chapter_chars = settings.refagent.chars or 1500
    if len(plan_list) != len(chapters_chars):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Количество глав в плане не совпадает с количеством распределённых страниц."
        )

    for idx, (plan_title, chapter_char_info) in enumerate(zip(plan_list, chapters_chars), start=1):
        chapter = Chapter(
            title=plan_title or f"Глава {idx}",
            position=idx,
            chars=chapter_char_info.get("chars", default_chapter_chars),
            essay_id=essay.id
        )
        session.add(chapter)

    # 5. Коммитим всё
    await session.commit()
    await session.refresh(essay)

    return {"essay_id": essay.id, "plan": plan}


@router.post("/{essay_id}/generate")
async def generate_essay_endpoint(
    essay_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Essay).where(Essay.id == essay_id, Essay.user_id == current_user.id)
    )
    essay = result.scalars().first()
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")

    # Проверка на уже запущенные задачи
    if essay.status in [EnumStatus.GENERATING, EnumStatus.GENERATED, EnumStatus.IN_PROGRESS, EnumStatus.STARTED]:
        return {"essay_id": essay.id, "status": essay.status, "task_id": essay.task_id}

    try:
        # Запускаем Celery задачу
        task = generate_essay.delay(essay_id)
        essay.task_id = task.id
        essay.status = EnumStatus.GENERATING

        await session.commit()
        await session.refresh(essay)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при запуске задачи: {str(e)}")

    return {"essay_id": essay.id, "status": essay.status, "task_id": essay.task_id}

@router.get("/{essay_id}/status")
async def get_essay_status(
    essay_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Essay).where(Essay.id == essay_id, Essay.user_id == current_user.id)
    )
    essay = result.scalars().first()
    if not essay:
        raise HTTPException(status_code=404, detail="Essay not found")

    # Проверка состояния Celery задачи
    if essay.task_id:
        celery_result = AsyncResult(essay.task_id, app=celery_app)
        if celery_result.state == "FAILURE":
            essay.status = EnumStatus.FAILURE
            session.add(essay)
            await session.commit()
            await session.refresh(essay)

    return {
        "essay_id": essay.id,
        "status": essay.status,
        "task_id": essay.task_id
    }

@router.get("/{essay_id}/chapters")
async def get_chapters(
    essay_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Проверяем, что эссе принадлежит пользователю
    result = await session.execute(
        select(Essay).where(
            Essay.id == essay_id,
            Essay.user_id == current_user.id
        )
    )
    essay = result.scalars().first()

    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Эссе не найдено или нет доступа"
        )

    # Получаем главы
    result = await session.execute(
        select(Chapter)
        .where(Chapter.essay_id == essay_id)
        .order_by(Chapter.position.asc())
    )

    chapters = result.scalars().all()

    return {
        "essay_id": essay_id,
        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "position": ch.position,
                "content": ch.content or None
            }
            for ch in chapters
        ]
    }


@router.put("/chapter/title/update")
async def update_chapter_title(
    data: UpdateChapterRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Ищем главу
    result = await session.execute(
        select(Chapter).where(Chapter.id == data.chapter_id)
    )
    chapter = result.scalars().first()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Глава не найдена"
        )

    # Проверяем, что глава принадлежит текущему пользователю
    result = await session.execute(
        select(Essay).where(Essay.id == chapter.essay_id)
    )
    essay = result.scalars().first()

    if not essay or essay.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой главе"
        )

    # Обновляем заголовок
    chapter.title = data.title

    # Сохраняем
    await session.commit()
    await session.refresh(chapter)

    return {
        "message": "Заголовок обновлён",
        "chapter": {
            "id": chapter.id,
            "title": chapter.title
        }
    }


@router.get("/{essay_id}")
async def get_essay_full(
    essay_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Essay)
        .options(
            selectinload(Essay.chapters),
            selectinload(Essay.essay_metadata)
        )
        .where(
            Essay.id == essay_id,
            Essay.user_id == current_user.id
        )
    )

    essay: Essay | None = result.scalars().first()

    if not essay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Эссе не найдено или нет доступа"
        )

    return {
        "id": essay.id,
        "topic": essay.topic,
        "page_count": essay.page_count,
        "language": getattr(essay, "language", None),
        "status": essay.status,

        "introduction": essay.introduction,
        "conclusion": essay.conclusion,
        "references": essay.references,

        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "position": ch.position,
                "content": ch.content or None
            }
            for ch in sorted(essay.chapters, key=lambda x: x.position)
        ],

        "metadata": None if not essay.essay_metadata else {
            "university": essay.essay_metadata.university,
            "faculty": essay.essay_metadata.faculty,
            "subject": essay.essay_metadata.subject,
            "performed_by": essay.essay_metadata.performed_by,
            "checked_by": essay.essay_metadata.checked_by,
            "group": essay.essay_metadata.group,
            "city": essay.essay_metadata.city,
            "year": essay.essay_metadata.year,
        }
    }
    
    
