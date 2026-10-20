from pydantic_ai import Agent
from pydantic_ai.models import Model

from app.tools.public_tools import search_text


def create_agent(model: Model | str) -> Agent[None, str]:
    agent = Agent(
        model=model,
        tools=[search_text],
        instructions="Ayuda a localizar contenido duplicado en un vault de notas",
    )
    return agent
