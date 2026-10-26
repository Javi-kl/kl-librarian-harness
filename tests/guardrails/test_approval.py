from pathlib import Path

import pytest

from app.guardrails.approval import EditApprovalError, prepare_edit_for_approval
from app.guardrails.state import ConversationState


def test_prepare_edit_for_approval__note_not_read__raises_without_changing_note(
    tmp_path: Path,
) -> None:
    note_path = tmp_path / "ollama.md"
    original_content = b"# Ollama\nEjecuta modelos localmente."
    note_path.write_bytes(original_content)
    state = ConversationState()

    with pytest.raises(EditApprovalError):
        prepare_edit_for_approval(
            vault_path=tmp_path,
            state=state,
            path="ollama.md",
            content="# Ollama\nContenido propuesto.",
        )
    assert note_path.read_bytes() == original_content


def test_prepare_edit_for_approval__note_changed_since_read__raises_without_changing_note(
    tmp_path: Path,
) -> None:
    note_path = tmp_path / "ollama.md"
    previous_content = "# Ollama\nVersión recibida por el agente."
    current_content = b"# Ollama\nCambio posterior del usuario."

    state = ConversationState(
        read_notes={"ollama.md": previous_content},
    )
    note_path.write_bytes(current_content)

    with pytest.raises(EditApprovalError):
        prepare_edit_for_approval(
            vault_path=tmp_path,
            state=state,
            path="ollama.md",
            content="# Ollama\nPropuesta basada en la versión anterior.",
        )

    assert note_path.read_bytes() == current_content
