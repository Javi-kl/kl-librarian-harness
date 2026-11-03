from pathlib import Path
from dataclasses import dataclass
from difflib import unified_diff
from collections.abc import Iterable

from app.guardrails.state import ConversationState
from app.shared.note_paths import NotePathError, resolve_note_path


class MutationApprovalError(Exception):
    """Indica que una modificación no puede prepararse o validarse para ejecución."""


@dataclass(frozen=True)
class EditProposal:
    path: str
    original_bytes: bytes
    content: str
    diff: str


@dataclass(frozen=True)
class DeleteProposal:
    path: str
    original_bytes: bytes


def _read_note_for_approval(
    vault_path: Path,
    state: ConversationState,
    path: str,
) -> bytes:

    if path not in state.read_notes:
        raise MutationApprovalError(
            "La nota no se ha devuelto al agente durante esta conversación."
        )

    previous_content = state.read_notes[path]
    try:
        note_path = resolve_note_path(vault_path, path)
    except NotePathError as error:
        raise MutationApprovalError(
            f"No se puede preparar la operación sobre la nota: {error.code}."
        ) from error

    original_bytes = note_path.read_bytes()
    original_content = original_bytes.decode("utf-8")
    # La búsqueda usa read_text, que normaliza los saltos de línea.
    current_content = original_content.replace("\r\n", "\n").replace("\r", "\n")

    if current_content != previous_content:
        raise MutationApprovalError("La nota ha cambiado desde la ultima lectura.")

    return original_bytes


def prepare_edit_for_approval(
    vault_path: Path,
    state: ConversationState,
    path: str,
    content: str,
) -> EditProposal:

    original_bytes = _read_note_for_approval(vault_path, state, path)
    original_content = original_bytes.decode("utf-8")

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


def prepare_delete_for_approval(
    vault_path: Path,
    state: ConversationState,
    path: str,
) -> DeleteProposal:

    original_bytes = _read_note_for_approval(vault_path, state, path)
    return DeleteProposal(
        path=path,
        original_bytes=original_bytes,
    )


def validate_proposals_unchanged(
    vault_path: Path,
    proposals: Iterable[EditProposal | DeleteProposal],
) -> None:
    """Comprueba las rutas y versiones aprobadas; rechaza cambios antes de ejecutar."""
    for proposal in proposals:
        try:
            note_path = resolve_note_path(vault_path, proposal.path)
        except NotePathError as error:
            raise MutationApprovalError(
                f"La ruta de la nota {proposal.path} ya no es válida: {error.code}."
            ) from error

        if note_path.read_bytes() != proposal.original_bytes:
            raise MutationApprovalError(
                f"La nota {proposal.path} cambió durante la revisión. "
                "No se ejecutarán las operaciones."
            )
