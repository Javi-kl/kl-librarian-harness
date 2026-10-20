from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

from app.shared.config import DeepSeekSettings
from app.agent.runtime import create_agent


def main() -> None:
    settings = DeepSeekSettings.model_validate({})

    model = OpenAIChatModel(
        settings.DEEPSEEK_MODEL,
        provider=DeepSeekProvider(
            api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
        ),
    )
    create_agent(model)


if __name__ == "__main__":
    main()
