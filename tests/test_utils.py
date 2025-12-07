import pytest

from src.refagent.utils import chars_to_page, distribute_pages_with_priority, parse_plan


def test_parse_plan_extracts_headings():
    html = """
    <document>
        <content>
            <ul>
                <li><h2>Первая глава</h2></li>
                <li><h2>Вторая глава</h2></li>
            </ul>
        </content>
    </document>
    """
    assert parse_plan(html) == ["Первая глава", "Вторая глава"]


def test_chars_to_page_converts_pages_to_counts():
    result = chars_to_page(2, chars=1000, full_chars=1200, words=250)
    assert result["chars"] == 2000
    assert result["full_chars"] == 2400
    assert result["words"] == 500


def test_distribute_pages_with_priority_uses_all_pages():
    distribution = distribute_pages_with_priority(
        total_pages=25,
        intro_pages=2,
        conclusion_pages=2,
        references_pages=1,
        number_of_chapters=4,
    )
    assert distribution["introduction"] == 2
    assert len(distribution["chapters"]) == 4
    total = (
        distribution["introduction"]
        + distribution["conclusion"]
        + distribution["references"]
        + sum(distribution["chapters"])
    )
    assert total == distribution["total_pages"] == 25


def test_distribute_pages_with_priority_raises_when_not_enough_pages():
    with pytest.raises(ValueError):
        distribute_pages_with_priority(
            total_pages=3, intro_pages=1, conclusion_pages=1, references_pages=1, number_of_chapters=2
        )
