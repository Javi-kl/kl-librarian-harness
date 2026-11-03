import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic_ai.messages import ToolCallPart

from app.guardrails.approval import (
    DeleteProposal,
    EditProposal,
    MutationApprovalError,
    prepare_delete_for_approval,
    prepare_edit_for_approval,
    validate_proposals_unchanged,
)
from app.guardrails.state import ConversationState
from app.observability.trace import record_decision

logger = logging.getLogger(__name__)


def review_proposal(
    proposal: EditProposal | DeleteProposal,
) -> Literal["approved", "rejected", "cancelled"] | None:
    """Muestra una propuesta y recoge la decisión; devuelve None si no hay cambios."""
    if isinstance(proposal, EditProposal):
        if not proposal.diff:
            logger.info("Sin cambios en %s. Se cancela la revisión.", proposal.path)
            return None

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
        return "cancelled"

    return "approved" if answer.lower() == "s" else "rejected"


def review_pending_operations(
    calls: Iterable[ToolCallPart],
    *,
    vault_path: Path,
    trace_path: Path,
    state: ConversationState,
    conversation_id: str,
) -> dict[str, EditProposal | DeleteProposal] | None:
    """Revisa y registra las decisiones; devuelve propuestas válidas o None al cancelar."""
    accepted_proposals: dict[str, EditProposal | DeleteProposal] = {}

    for call in calls:
        if call.tool_name not in {"edit_note", "delete_note"}:
            logger.warning("Solicitud pendiente no soportada: %s", call.tool_name)
            return None

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
                "No se puede preparar la operación de %s: %s", args["path"], error
            )
            return None

        decision = review_proposal(proposal)
        if decision is None:
            return None

        try:
            record_decision(
                trace_path,
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
            return None

        if decision == "cancelled":
            logger.info("Revisión cancelada. No se ha ejecutado ninguna operación.")
            return None
        if decision == "rejected":
            logger.info("Operación rechazada. No se ha ejecutado ninguna operación.")
            return None

        accepted_proposals[call.tool_call_id] = proposal

    try:
        validate_proposals_unchanged(vault_path, accepted_proposals.values())
    except (MutationApprovalError, OSError) as error:
        logger.warning("No se pueden ejecutar las operaciones: %s", error)
        return None

    return accepted_proposals
