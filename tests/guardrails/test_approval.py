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


def test_prepare_edit_for_approval__unchanged_read_note__returns_proposal_without_writing(
    tmp_path: Path,
) -> None:
    note_path = tmp_path / "ollama.md"
    original_content = "# Ollama\nTexto original.\n"
    proposed_content = "# Ollama\nTexto actualizado.\n"
    original_bytes = original_content.encode("utf-8")
    note_path.write_bytes(original_bytes)
    state = ConversationState(
        read_notes={"ollama.md": original_content},
    )
    proposal = prepare_edit_for_approval(
        vault_path=tmp_path,
        state=state,
        path="ollama.md",
        content=proposed_content,
    )
    assert proposal.path == "ollama.md"
    assert proposal.original_bytes == original_bytes
    assert proposal.content == proposed_content
    assert "-Texto original.\n" in proposal.diff
    assert "+Texto actualizado.\n" in proposal.diff
    assert note_path.read_bytes() == original_bytes


def test_prepare_edit_for_approval__note_replaced_with_symlink__rejects_without_changing_target(
    tmp_path: Path,
) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    original_content = "# Ollama\nTexto recibido por el agente.\n"
    original_bytes = original_content.encode("utf-8")
    state = ConversationState(
        read_notes={"ollama.md": original_content},
    )
    outside_path = tmp_path / "outside.md"
    outside_path.write_bytes(original_bytes)
    note_path = vault_path / "ollama.md"
    note_path.symlink_to(outside_path)
    with pytest.raises(EditApprovalError):
        prepare_edit_for_approval(
            vault_path=vault_path,
            state=state,
            path="ollama.md",
            content="# Ollama\nContenido propuesto.\n",
        )
    assert note_path.is_symlink()
    assert outside_path.read_bytes() == original_bytes
