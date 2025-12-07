from langchain_openai import ChatOpenAI
from src.config import settings


class PlanAgent:
    def __init__(self, model=settings.refagent.model_name):
        self.model = ChatOpenAI(
            openai_api_key=settings.refagent.openai_api_key,
            temperature=settings.refagent.temperature,
            model=model
        )

    def generate_plan(self, topic: str, language: str = "ru", chapters_count: int = 3) -> str:
        prompt = f"""
Ты — интеллектуальный агент, который составляет план академического реферата
строго в формате XML.

Тема реферата: "{topic}"
Язык: {language}

Требования:
1. Ответ должен быть строго в формате:

<document>
    <content>
        <ul>
            <li><h2>1. Название главы...</h2></li>
            <li><h2>2. Название главы...</h2></li>
            ...
        </ul>
    </content>
</document>

2. Перечисляй только названия глав в тегах <h2>, без текста внутри главы.
3. Количество глав: {chapters_count}.
4. Заключение и источники должны быть последними двумя элементами списка.
5. Никаких подглав, абзацев или лишних тегов.
6. Ты должен написать план только для глав например: введение, заключение и источники писать не нужно 
- Не используй markdown
"""

        result = self.model.invoke(prompt)
        return result.content
