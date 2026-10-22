import logging

from pydantic_ai import ModelMessage, ToolCallPart
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.usage import UsageLimits

from app.shared.config import DeepSeekSettings
from app.agent.runtime import create_agent

logger = logging.getLogger(__name__)


def main() -> None:
    settings = DeepSeekSettings.model_validate({})

    model = OpenAIChatModel(
        settings.DEEPSEEK_MODEL,
        provider=DeepSeekProvider(
            api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
        ),
        settings=OpenAIChatModelSettings(thinking=False),
    )
    agent = create_agent(model)
    history: list[ModelMessage] = []
    logger.info("Asistente de KB. Escribe 'salir' para terminar.")
    while True:
        try:
            user_message = input("\nTú> ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("Conversación terminada.")
            break
        if user_message.lower() == "salir":
            break
        if not user_message:
            continue
        result = agent.run_sync(
            user_message,
            message_history=history,
            usage_limits=UsageLimits(
                request_limit=5,
                tool_calls_limit=3,
            ),
        )
        history = result.all_messages()
        logger.info("Agente:\n%s", result.output)
        for message in result.new_messages():
            for part in message.parts:
                if isinstance(part, ToolCallPart):
                    logger.info(
                        "Tool solicitada: %s; argumentos: %s",
                        part.tool_name,
                        part.args,
                    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
