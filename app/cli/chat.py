import logging
from uuid import uuid4

from pydantic_ai import (
    Agent,
    DeferredToolRequests,
    DeferredToolResults,
    ModelMessage,
    ToolCallPart,
)
from pydantic_ai.usage import UsageLimits

from app.cli.review import review_pending_operations
from app.guardrails.state import ConversationState
from app.shared.config import get_settings

logger = logging.getLogger(__name__)


def run_chat(agent: Agent[ConversationState, str | DeferredToolRequests]) -> None:
    """Gestiona la conversación por terminal con el agente recibido."""
    history: list[ModelMessage] = []
    logger.info("Asistente de KB. Escribe 'salir' para terminar.")
    state = ConversationState()
    conversation_id = str(uuid4())
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
            conversation_id=conversation_id,
            deps=state,
            usage_limits=UsageLimits(
                request_limit=5,
                tool_calls_limit=3,
            ),
        )
        history = result.all_messages()

        while isinstance(result.output, DeferredToolRequests):
            config = get_settings()
            accepted_proposals = review_pending_operations(
                result.output.approvals,
                vault_path=config.KB_VAULT_PATH,
                trace_path=config.TRACE_PATH,
                state=state,
                conversation_id=conversation_id,
            )
            if accepted_proposals is None:
                return

            approvals = DeferredToolResults(
                approvals={call_id: True for call_id in accepted_proposals}
            )

            result = agent.run_sync(
                message_history=history,
                conversation_id=conversation_id,
                deps=state,
                deferred_tool_results=approvals,
                usage=result.usage,
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
