import logging
from uuid import uuid4

from pydantic_ai import (
    DeferredToolRequests,
    DeferredToolResults,
    ModelMessage,
    ToolCallPart,
)
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.usage import UsageLimits

from app.guardrails.approval import (
    DeleteProposal,
    EditProposal,
    MutationApprovalError,
    prepare_delete_for_approval,
    prepare_edit_for_approval,
)
from app.guardrails.state import ConversationState
from app.observability.trace import record_decision
from app.shared.config import DeepSeekSettings, get_settings
from app.shared.note_paths import NotePathError, resolve_note_path
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
            vault_path = config.KB_VAULT_PATH
            accepted_proposal: dict[str, EditProposal | DeleteProposal] = {}

            for call in result.output.approvals:
                if call.tool_name not in {"edit_note", "delete_note"}:
                    logger.warning(
                        "Solicitud pendiente no soportada: %s",
                        call.tool_name,
                    )
                    return

                args = call.args_as_dict()

                try:
                    proposal: EditProposal | DeleteProposal
                    if call.tool_name == "edit_note":
                        proposal = prepare_edit_for_approval(
                            vault_path=vault_path,
                            state=state,
                            path=args["path"],
                            content=args["content"],
                        )
                    else:
                        proposal = prepare_delete_for_approval(
                            vault_path=vault_path,
                            state=state,
                            path=args["path"],
                        )

                except (MutationApprovalError, OSError, UnicodeError) as error:
                    logger.warning(
                        "No se puede preparar la operación de %s: %s",
                        args["path"],
                        error,
                    )
                    return

                if isinstance(proposal, EditProposal):
                    if not proposal.diff:
                        logger.info(
                            "Sin cambios en %s. Se cancela la revisión.", proposal.path
                        )
                        return

                    logger.info(
                        "Cambio propuesto en %s:\n%s",
                        proposal.path,
                        proposal.diff,
                    )
                    question = f"¿Aplicar la edición de {proposal.path}? [s/N] "
                else:
                    logger.info(
                        "Borrado propuesto: mover %s a la papelera del vault.",
                        proposal.path,
                    )
                    question = f"¿Mover {proposal.path} a la papelera? [s/N] "

                try:
                    answer = input(question).strip()
                except (EOFError, KeyboardInterrupt):
                    decision = "cancelled"
                else:
                    decision = "approved" if answer.lower() == "s" else "rejected"

                try:
                    record_decision(
                        config.TRACE_PATH,
                        conversation_id=conversation_id,
                        call_id=call.tool_call_id,
                        tool_name=call.tool_name,
                        note_path=proposal.path,
                        decision=decision,
                    )
                except (OSError, UnicodeError) as error:
                    logger.error(
                        "No se pudo registrar la decisión. "
                        "No se ha ejecutado ninguna operación pendiente: %s",
                        error,
                    )
                    return

                if decision == "cancelled":
                    logger.info(
                        "Revisión cancelada. No se ha ejecutado ninguna operación."
                    )
                    return
                if decision == "rejected":
                    logger.info(
                        "Operación rechazada. No se ha ejecutado ninguna operación."
                    )
                    return
                accepted_proposal[call.tool_call_id] = proposal

            try:
                for proposal in accepted_proposal.values():
                    note_path = resolve_note_path(vault_path, proposal.path)

                    if note_path.read_bytes() != proposal.original_bytes:
                        logger.warning(
                            "La nota %s cambió durante la revisión. No se ejecutarán las operaciones.",
                            proposal.path,
                        )
                        return
            except (NotePathError, OSError) as error:
                logger.warning("No se pueden ejecutar las operaciones: %s", error)
                return

            approvals = DeferredToolResults(
                approvals={call_id: True for call_id in accepted_proposal}
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
