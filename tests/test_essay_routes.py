from types import SimpleNamespace

import pytest
from sqlalchemy import select

import src.routes.essay as essay_routes
from src.models.essay import Chapter, EnumStatus, Essay
from src.refagent.utils import chars_to_page, distribute_pages_with_priority


@pytest.fixture
def stub_plan_agent(monkeypatch):
    def _generate(self, topic, chapters_count, language):
        items = "".join(f"<li><h2>Глава {idx}</h2></li>" for idx in range(1, chapters_count + 1))
        return f"<document><content><ul>{items}</ul></content></document>"

    monkeypatch.setattr("src.refagent.agents.plan_agent.PlanAgent.generate_plan", _generate)


@pytest.fixture
def stub_celery_delay(monkeypatch):
    def fake_delay(essay_id: int):
        return SimpleNamespace(id=f"task-{essay_id}")

    monkeypatch.setattr(essay_routes.generate_essay, "delay", fake_delay)


@pytest.mark.anyio
async def test_generate_plan_creates_essay_with_distributed_chars(
    client,
    user_factory,
    auth_override,
    db_session,
    stub_plan_agent,
):
    user = await user_factory()
    auth_override(user)
    payload = {
        "topic": "Программирование",
        "checked_by": "Преподаватель",
        "subject": "Информатика",
        "page_count": 20,
        "chapters_count": 4,
        "language": "ru",
    }

    response = await client.post("/api/v1/essays/plan/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    essay_id = data["essay_id"]
    assert data["plan"]

    essay = await db_session.get(Essay, essay_id)
    assert essay.chapter_count == payload["chapters_count"]

    pages = 1
    pages_priority = distribute_pages_with_priority(
        total_pages=payload["page_count"],
        intro_pages=pages,
        conclusion_pages=pages,
        references_pages=1,
        number_of_chapters=payload["chapters_count"],
    )
    intro_expected = chars_to_page(pages_priority["introduction"])["chars"]
    assert essay.introduction_chars_count == intro_expected

    chapters = await db_session.execute(select(Chapter).where(Chapter.essay_id == essay_id).order_by(Chapter.position))
    chapters = chapters.scalars().all()
    assert len(chapters) == payload["chapters_count"]
    for idx, chapter in enumerate(chapters):
        expected_chars = chars_to_page(pages_priority["chapters"][idx])["chars"]
        assert chapter.chars == expected_chars


@pytest.mark.anyio
async def test_generate_essay_endpoint_updates_status(
    client,
    user_factory,
    auth_override,
    stub_plan_agent,
    stub_celery_delay,
    db_session,
):
    user = await user_factory()
    auth_override(user)

    response = await client.post(
        "/api/v1/essays/plan/generate",
        json={
            "topic": "Тест",
            "checked_by": "Учитель",
            "subject": "Информатика",
            "page_count": 20,
            "chapters_count": 3,
            "language": "ru",
        },
    )
    essay_id = response.json()["essay_id"]

    generate_response = await client.post(f"/api/v1/essays/{essay_id}/generate")
    assert generate_response.status_code == 200
    assert generate_response.json()["task_id"] == f"task-{essay_id}"

    essay = await db_session.get(Essay, essay_id)
    assert essay.status == EnumStatus.GENERATING


@pytest.mark.anyio
async def test_status_endpoint_returns_current_state(
    client,
    user_factory,
    auth_override,
    stub_plan_agent,
    db_session,
):
    user = await user_factory()
    auth_override(user)

    response = await client.post(
        "/api/v1/essays/plan/generate",
        json={
            "topic": "Алгоритмы",
            "checked_by": "Научный руководитель",
            "subject": "Информатика",
            "page_count": 20,
            "chapters_count": 2,
            "language": "ru",
        },
    )
    essay_id = response.json()["essay_id"]

    essay = await db_session.get(Essay, essay_id)
    essay.status = EnumStatus.GENERATED
    await db_session.commit()

    status_response = await client.get(f"/api/v1/essays/{essay_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == EnumStatus.GENERATED
