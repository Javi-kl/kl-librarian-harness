from pathlib import Path
from dataclasses import dataclass
from difflib import unified_diff

from app.guardrails.state import ConversationState
from app.shared.note_paths import NotePathError, resolve_note_path


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
    try:
        note_path = resolve_note_path(vault_path, path)
    except NotePathError as error:
        raise EditApprovalError(
            f"No se puede preparar la edición de la nota: {error.code}."
        ) from error

    original_bytes = note_path.read_bytes()
    original_content = original_bytes.decode("utf-8")
    # La búsqueda usa read_text, que normaliza los saltos de línea.
    current_content = original_content.replace("\r\n", "\n").replace("\r", "\n")

    if current_content != previous_content:
        raise EditApprovalError("La nota ha cambiado desde la ultima lectura.")

    diff = "".join(
        unified_diff(
            original_content.splitlines(keepends=True),
            content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )

    return EditProposal(
        path=path,
        original_bytes=original_bytes,
        content=content,
        diff=diff,
    )
