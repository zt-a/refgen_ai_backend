from langchain_openai import ChatOpenAI
from src.config import settings

class ConclusionAgent:
    def __init__(self, model=settings.refagent.model_name):
        self.model = ChatOpenAI(
            openai_api_key=settings.refagent.openai_api_key,
            temperature=settings.refagent.temperature,
            model=model
        )

    def write(self, 
                    topic: str, 
                    language: str = "ru", 
                    chars: int = settings.refagent.chars or 1500, 
                    full_chars: int = settings.refagent.full_chars or 2000,
                    words: int = settings.refagent.words or 300
):
        prompt = f"""
Ты — ИИ для написания Заключения академического реферата.

Тема: "{topic}"
Язык: {language}
Объём: {chars} символов.
Объём с пробелами: {full_chars} символов.
Объём: {words} слов.

Требования:
- кратко подвести итог исследования
- показать значимость темы
- не повторять текст введения дословно
- академический стиль
- не дели на подглавы
- не добавляй слово "Заключение" в начале, сразу текст контента
- Не добавляй тег <meta> или что-либо кроме <content> и <formulas>
- В тексте используй только теги: h1, h2, h3, p, ul, ol, table
- Если есть математические выражения, вставляй <formula id="fX"/> в тексте
- Все формулы должны быть в блоке <formulas> в виде <latex id="fX">...</latex>
- Если формул нет — блок <formulas> оставь пустым, но не убирай его
- Формат ответа строго XML/HTML, без лишних пояснений и текста
- Не используй markdown

Выведи результат строго в формате:

<document>
    <content>
        ...текст заключения с тегами h1, h2, h3, p, ul, ol, table...
        ...формулы как <formula id="fX"/>...
    </content>
    <formulas>
        ...формулы как <latex id="fX">...</latex>...
    </formulas>
</document>
"""


        result = self.model.invoke(prompt)
        return result.content
