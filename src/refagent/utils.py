from src.config import settings
from bs4 import BeautifulSoup

def parse_plan(data):
    soup = BeautifulSoup(data, 'html.parser')
    plan = []
    for item in soup.find_all('h2'):
        plan.append(item.text.strip())
    return plan


def chars_to_page(
    page: int,
    chars: int = settings.refagent.chars or 1500,
    full_chars: int = settings.refagent.full_chars or 2000,
    words: int = settings.refagent.words or 300, 
):
    """
    Переводит количество страниц в примерное количество символов и слов.

    Аргументы:
    - page (int): количество страниц
    - chars (int): количество символов на страницу (по умолчанию 1500)
    - full_chars (int): количество символов с учётом пробелов и знаков (по умолчанию 2000)
    - words (int): количество слов на страницу (по умолчанию 300)

    Возвращает:
    dict с ключами:
        - 'chars': количество символов
        - 'full_chars': количество символов с пробелами
        - 'words': количество слов
    """
    return {
        "chars": chars * page,
        "full_chars": full_chars * page,
        "words": words * page
    }
    
    
    
def distribute_pages_with_priority(
    total_pages: int,
    intro_pages: int = 1,
    conclusion_pages: int = 1,
    references_pages: int = 1,
    number_of_chapters: int = 3
):
    """
    Распределяет страницы по разделам реферата с приоритетом глав.
    
    Логика:
    1. Введение, заключение и источники получают фиксированное минимальное количество страниц.
    2. Остаток страниц идёт на главы.
    3. Проверяется, чтобы каждая глава получила больше страниц, чем введение, заключение и источники.
    4. Остаток распределяется равномерно между всеми главами.

    Аргументы:
        total_pages (int): Общее количество страниц реферата
        intro_pages (int): Страницы для введения
        conclusion_pages (int): Страницы для заключения
        references_pages (int): Страницы для источников
        number_of_chapters (int): Количество глав

    Возвращает:
        dict с распределением страниц:
            - 'introduction'
            - 'chapters' (список количества страниц на каждую главу)
            - 'conclusion'
            - 'references'
            - 'total_pages'
    """
    if number_of_chapters <= 0:
        raise ValueError("Количество глав должно быть положительным")

    min_non_chapter_pages = intro_pages + conclusion_pages + references_pages

    if min_non_chapter_pages >= total_pages:
        raise ValueError("Недостаточно страниц для глав!")

    # Остаток страниц для глав
    pages_for_chapters = total_pages - min_non_chapter_pages
    # Распределяем целые страницы по главам: базовое количество и остаток
    pages_per_chapter = pages_for_chapters // number_of_chapters
    if pages_per_chapter == 0:
        raise ValueError("Слишком много глав для указанного количества страниц.")
    remainder = pages_for_chapters % number_of_chapters

    # Проверка, что главы больше, чем остальные разделы
    max_non_chapter_pages = max(intro_pages, conclusion_pages, references_pages)
    if pages_per_chapter <= max_non_chapter_pages:
        raise ValueError(
            f"Слишком мало страниц для глав. Каждая глава ({pages_per_chapter}) должна быть больше, чем введение, заключение или источники ({max_non_chapter_pages})."
        )

    chapters_distribution = [pages_per_chapter] * number_of_chapters
    for i in range(remainder):
        chapters_distribution[i] += 1

    # Возвращаем количество страниц на главу (целое). Если остались лишние страницы,
    # они будут распределены вручную при построении текста (в текущей версии
    # используем равномерное значение для всех глав).
    return {
        "introduction": intro_pages,
        "chapters": chapters_distribution,
        "conclusion": conclusion_pages,
        "references": references_pages,
        "total_pages": total_pages,
        "remainder_pages": int(remainder),
    }
