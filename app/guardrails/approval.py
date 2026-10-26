from pathlib import Path
from dataclasses import dataclass

from app.guardrails.state import ConversationState


class EditApprovalError(Exception):
    """Indica que una edición no puede prepararse para aprobación."""


@dataclass(frozen=True)
class EditProposal:
    path: str
    original_bytes: bytes
    content: str
    diff: str


def prepare_edit_for_approval(
    vault_path: Path,
    state: ConversationState,
    path: str,
    content: str,
) -> EditProposal:
    if path not in state.read_notes:
        raise EditApprovalError(
            "La nota no se ha devuleto al agente durante esta conversación."
        )

    previous_content = state.read_notes[path]
    note_path = vault_path / path
    current_content = note_path.read_text(encoding="utf-8")

    if current_content != previous_content:
        raise EditApprovalError("La nota ha cambiado desde la ultima lectura.")

    raise NotImplementedError
