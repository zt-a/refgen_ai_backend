from langchain_openai import ChatOpenAI
from src.config import settings

class IntroductionAgent:
    def __init__(self, model=settings.refagent.model_name):
        self.model = ChatOpenAI(
            openai_api_key=settings.refagent.openai_api_key,
            temperature=settings.refagent.temperature,
            model=model
        )

    def write(self, 
              topic: str, 
              language: str = "ru", 
              chars: int = settings.refagent.chars or 1500
    ) -> str:
        prompt = f"""
Ты — академический модуль для написания Введения реферата. 
Тема: "{topic}"
Язык: {language}
Объём: {chars} символов.

Требования:
- академический стиль
- без выдуманных фактов
- объяснить актуальность темы
- раскрыть цель и задачи исследования
- не писать план, только связный текст введения
- Не добавляй слово "Введение", сразу начинай контент
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
        ...твой текст с тегами h1, h2, h3, p, ul, ol, table...
        ...формулы как <formula id="fX"/>...
    </content>
    <formulas>
        ...формулы как <latex id="fX">...</latex>...
    </formulas>
</document>
"""

        result = self.model.invoke(prompt)
        return result.content
