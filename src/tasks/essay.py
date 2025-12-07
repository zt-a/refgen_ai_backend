from sqlalchemy.orm import selectinload

from src.config import settings
from src.models.essay import EnumStatus, Essay
from src.celery_app import celery_app
from src.database import SyncSessionLocal
from src.refagent.agents.introduction_agent import IntroductionAgent
from src.refagent.agents.conclusion_agent import ConclusionAgent
from src.refagent.agents.references_agent import ReferencesAgent
from src.refagent.agents.chapter_agent import ChapterAgent


@celery_app.task(bind=True)
def generate_essay(self, essay_id: int):
    introduction_agent = IntroductionAgent()
    conclusion_agent = ConclusionAgent()
    references_agent = ReferencesAgent()
    chapter_agent = ChapterAgent()

    chars_per_page = settings.refagent.chars or 1500
    full_chars_per_page = settings.refagent.full_chars or 2000
    words_per_page = settings.refagent.words or 300

    with SyncSessionLocal() as db:
        try:
            essay = db.query(Essay).options(selectinload(Essay.chapters))\
                      .filter(Essay.id == essay_id).first()
            if not essay:
                return {"essay_id": essay_id, "status": EnumStatus.FAILURE, "message": "Essay not found"}

            essay.status = EnumStatus.GENERATING
            db.commit()
            db.refresh(essay)

            # Генерация частей эссе
            if essay.introduction_chars_count and essay.introduction_chars_count > 0:
                essay.introduction = introduction_agent.write(
                    essay.topic, essay.language, essay.introduction_chars_count
                )
            if essay.conclusion_chars_count and essay.conclusion_chars_count > 0:
                essay.conclusion = conclusion_agent.write(
                    essay.topic, essay.language, essay.conclusion_chars_count
                )
            if essay.references_chars_count and essay.references_chars_count > 0:
                essay.references = references_agent.write(
                    essay.topic, essay.language, essay.references_chars_count
                )

            # Генерация глав
            for chapter in essay.chapters:
                if chapter.chars and chapter.chars > 0:
                    approximate_pages = max(chapter.chars / chars_per_page, 1)
                    chapter_full_chars = int(full_chars_per_page * approximate_pages)
                    chapter_words = int(words_per_page * approximate_pages)
                    chapter.content = chapter_agent.write_chapter(
                        topic=essay.topic,
                        chapter_title=chapter.title,
                        position=chapter.position,
                        language=essay.language,
                        chars=chapter.chars,
                        full_chars=chapter_full_chars,
                        words=chapter_words
                    )

            # Обновление статуса
            essay.status = EnumStatus.GENERATED
            db.commit()
            db.refresh(essay)

            return {"essay_id": essay.id, "status": essay.status}

        except Exception as e:
            db.rollback()
            # Логирование через logger или self.logger
            print(f"[ERROR] Failed to generate essay {essay_id}: {e}")
            return {"essay_id": essay_id, "status": EnumStatus.FAILURE, "message": str(e)}
