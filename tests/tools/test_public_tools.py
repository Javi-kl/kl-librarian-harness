from pathlib import Path

import pytest

from app.shared.config import get_settings
from app.tools.delete_note import DeleteNoteError
from app.tools.edit_note import EditNoteError
from app.tools.public_tools import delete_note, edit_note
from app.tools.schemas import (
    DeleteNoteFailure,
    DeleteNoteSuccess,
    EditNoteFailure,
    EditNoteSuccess,
)


def test_edit_note__existing_note__returns_verified_success(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = "pages/kubernetes.md"
    content = "# Edición\r\nPrimera línea con café.\nÚltima línea: niño."
    expected_content = content.encode("utf-8")
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_vault_path))
    monkeypatch.chdir(tmp_vault_path)
    get_settings.cache_clear()

    try:
        result = edit_note(path, content)
    finally:
        get_settings.cache_clear()

    assert result == EditNoteSuccess(
        ok=True, path=path, verified=True, bytes=len(expected_content)
    )
    assert (tmp_vault_path / path).read_bytes() == expected_content


@pytest.mark.parametrize(
    "error_codes",
    [
        pytest.param(["note_not_found"], id="note_not_found"),
        pytest.param(["invalid_path"], id="invalid_path"),
        pytest.param(["permission_denied"], id="permission_denied"),
        pytest.param(["file_operation_failed"], id="file_operation_failed"),
        pytest.param(
            ["temporary_verification_failed"], id="temporary_verification_failed"
        ),
        pytest.param(["final_verification_failed"], id="final_verification_failed"),
        pytest.param(["temporary_cleanup_failed"], id="temporary_cleanup_failed"),
        pytest.param(
            ["temporary_verification_failed", "temporary_cleanup_failed"],
            id="operation_and_cleanup_failed",
        ),
    ],
)
def test_edit_note__expected_error__returns_failure_with_error_codes(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch, error_codes: list[str]
):
    path = "pages/kubernetes.md"

    def fail_replace_note_content(vault_path: Path, path: str, content: str) -> int:
        raise EditNoteError(error_codes)

    monkeypatch.setattr(
        "app.tools.public_tools.replace_note_content", fail_replace_note_content
    )
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_vault_path))
    monkeypatch.chdir(tmp_vault_path)
    get_settings.cache_clear()

    try:
        result = edit_note(path, "# New content")
    finally:
        get_settings.cache_clear()

    assert result == EditNoteFailure(ok=False, path=path, error=error_codes)


def test_delete_note__existing_note__returns_success_with_trash_path(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = "pages/kubernetes.md"
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_vault_path))
    monkeypatch.chdir(tmp_vault_path)
    get_settings.cache_clear()

    try:
        result = delete_note(path)
    finally:
        get_settings.cache_clear()

    assert result == DeleteNoteSuccess(
        ok=True, path=path, trash_path="trash/kubernetes.md.trash"
    )
    assert not (tmp_vault_path / path).exists()


@pytest.mark.parametrize(
    "error_codes",
    [
        pytest.param(["note_not_found"], id="note_not_found"),
        pytest.param(["invalid_path"], id="invalid_path"),
        pytest.param(["permission_denied"], id="permission_denied"),
        pytest.param(["file_operation_failed"], id="file_operation_failed"),
    ],
)
def test_delete_note__expected_error__returns_failure_with_error_codes(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch, error_codes: list[str]
):
    def fail_move_note_to_trash(vault_path: Path, path: str) -> str:
        raise DeleteNoteError(error_codes)

    monkeypatch.setattr(
        "app.tools.public_tools.move_note_to_trash", fail_move_note_to_trash
    )
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_vault_path))
    monkeypatch.chdir(tmp_vault_path)
    get_settings.cache_clear()

    try:
        result = delete_note("pages/kubernetes.md")
    finally:
        get_settings.cache_clear()

    assert result == DeleteNoteFailure(
        ok=False, path="pages/kubernetes.md", error=error_codes
    )
