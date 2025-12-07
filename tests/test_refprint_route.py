from pathlib import Path

import pytest

import src.routes.refprint as refprint_route
from src.config import settings
from src.models.essay import Chapter, EnumLanguage, EnumStatus, Essay, EssayMetadata


def _xml_block(text: str) -> str:
    return f"<document><content><p>{text}</p></content><formulas></formulas></document>"


@pytest.mark.anyio
async def test_refprint_generates_docx_file(
    user_factory,
    db_session,
    tmp_path,
    monkeypatch,
):
    user = await user_factory()

    essay = Essay(
        topic="Тестовый реферат",
        page_count=10,
        status=EnumStatus.GENERATED,
        language=EnumLanguage.RU,
        chapter_count=2,
        introduction=_xml_block("Введение"),
        introduction_chars_count=1000,
        conclusion=_xml_block("Заключение"),
        conclusion_chars_count=800,
        references=_xml_block("Источники"),
        references_chars_count=500,
        user_id=user.id,
    )
    db_session.add(essay)
    await db_session.flush()

    metadata = EssayMetadata(
        essay_id=essay.id,
        university="Test University",
        faculty="Faculty",
        subject="Subject",
        course=1,
        performed_by="Студент",
        checked_by="Преподаватель",
        group="A1",
        city="Moscow",
    )
    db_session.add(metadata)

    chapters = [
        Chapter(
            title="Глава 1",
            position=1,
            chars=1500,
            content=_xml_block("Контент главы 1"),
            essay_id=essay.id,
        ),
        Chapter(
            title="Глава 2",
            position=2,
            chars=1500,
            content=_xml_block("Контент главы 2"),
            essay_id=essay.id,
        ),
    ]
    db_session.add_all(chapters)
    await db_session.commit()

    monkeypatch.setattr(settings.refprint, "save_dir", Path(tmp_path))
    monkeypatch.setattr(refprint_route, "SAVE_DIR", Path(tmp_path))

    class DummyFrontPage:
        def __init__(self, **kwargs):
            self.doc = kwargs["doc"]

        def write(self):
            return self.doc

    class DummyRefPrint:
        def __init__(self, doc):
            self.doc = doc

        def add_footer(self):
            pass

        def ref_add(self, data):
            pass

        def ref_print(self):
            return self.doc

    monkeypatch.setattr(refprint_route, "FrontPage", DummyFrontPage)
    monkeypatch.setattr(refprint_route, "RefPrint", DummyRefPrint)

    response = await refprint_route.refprint(
        essay_id=essay.id,
        current_user=user,
        session=db_session,
    )
    assert response.status_code == 200 if hasattr(response, "status_code") else True
    saved_file = Path(tmp_path) / f"{essay.id}_{essay.topic}.docx"
    assert saved_file.exists()
