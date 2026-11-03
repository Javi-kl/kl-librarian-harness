import logging

from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.deepseek import DeepSeekProvider

from app.agent.runtime import create_agent
from app.cli.chat import run_chat
from app.shared.config import DeepSeekSettings


def main() -> None:
    """Construye el agente y arranca la conversación por terminal."""
    settings = DeepSeekSettings.model_validate({})
    model = OpenAIChatModel(
        settings.DEEPSEEK_MODEL,
        provider=DeepSeekProvider(
            api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
        ),
        settings=OpenAIChatModelSettings(thinking=False),
    )
    agent = create_agent(model)
    run_chat(agent)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
