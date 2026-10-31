import logging

from pydantic_ai import DeferredToolRequests, ModelMessage, ToolCallPart
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.usage import UsageLimits

from app.guardrails.approval import EditApprovalError, prepare_edit_for_approval
from app.guardrails.state import ConversationState
from app.shared.config import DeepSeekSettings, get_settings
from app.agent.runtime import create_agent

logger = logging.getLogger(__name__)


def main() -> None:
    settings = DeepSeekSettings.model_validate({})

    # TODO Llevarme los ajustes de  modelos a otro sitio...
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
    state = ConversationState()
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
            deps=state,
            usage_limits=UsageLimits(
                request_limit=5,
                tool_calls_limit=3,
            ),
        )
        history = result.all_messages()

        if isinstance(result.output, DeferredToolRequests):
            vault_path = get_settings().KB_VAULT_PATH

            for call in result.output.approvals:
                if call.tool_name != "edit_note":
                    logger.warning(
                        "Solicitud pendiente no soportada: %s",
                        call.tool_name,
                    )
                    continue

                args = call.args_as_dict()

                try:
                    proposal = prepare_edit_for_approval(
                        vault_path=vault_path,
                        state=state,
                        path=args["path"],
                        content=args["content"],
                    )
                except (EditApprovalError, OSError, UnicodeError) as error:
                    logger.warning(
                        "No se puede preparar la edición de %s: %s",
                        args["path"],
                        error,
                    )
                    continue
                if proposal.diff:
                    logger.info(
                        "Cambio propuesto en %s:\n%s",
                        proposal.path,
                        proposal.diff,
                    )
                else:
                    logger.info("Sin cambios en %s.", proposal.path)

            logger.info("No se ha ejecutado ninguna edición.")
            break

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
