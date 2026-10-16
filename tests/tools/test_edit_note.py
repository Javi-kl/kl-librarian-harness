from pathlib import Path

import pytest

from app.shared.config import get_settings
from app.tools.edit_note import EditNoteError, edit_note, replace_note_content
from app.tools.schemas import EditNoteFailure, EditNoteSuccess


def test_replace_note_content__existing_note__replaces_full_content(
    tmp_vault_path: Path,
):
    path = "pages/kubernetes.md"
    content = "# Kubernetes\nContenido nuevo."

    replace_note_content(tmp_vault_path, path, content)

    assert (tmp_vault_path / path).read_bytes() == content.encode("utf-8")


def test_replace_note_content__missing_note__raises_without_writing_file(
    tmp_vault_path: Path,
):
    path = "pages/missing.md"

    with pytest.raises(EditNoteError) as error:
        replace_note_content(tmp_vault_path, path, "# New content")

    assert error.value.codes == ["note_not_found"]
    assert not (tmp_vault_path / path).exists()


@pytest.mark.parametrize("target_kind", ["non_markdown_file", "directory"])
def test_replace_note_content__invalid_target__raises_without_writing_file(
    tmp_vault_path: Path, target_kind: str
):
    path = (
        "pages/settings.txt"
        if target_kind == "non_markdown_file"
        else "pages/folder.md"
    )
    file_path = tmp_vault_path / path
    original_content = b"Original settings"
    if target_kind == "directory":
        file_path.mkdir()
    else:
        file_path.write_bytes(original_content)

    with pytest.raises(EditNoteError) as error:
        replace_note_content(tmp_vault_path, path, "# New content")

    assert error.value.codes == ["invalid_path"]
    if target_kind == "directory":
        assert file_path.is_dir()
    else:
        assert file_path.read_bytes() == original_content


@pytest.mark.parametrize("path_kind", ["absolute", "parent_segment", "symlink"])
def test_replace_note_content__forbidden_path__raises_without_writing_file(
    tmp_path: Path, path_kind: str
):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    outside_path = tmp_path / "outside.md"
    original_content = b"Original content"
    outside_path.write_bytes(original_content)

    paths = {
        "absolute": str(outside_path),
        "parent_segment": "../outside.md",
        "symlink": "linked.md",
    }
    if path_kind == "symlink":
        (vault_path / "linked.md").symlink_to(outside_path)

    with pytest.raises(EditNoteError) as error:
        replace_note_content(vault_path, paths[path_kind], "# New content")

    assert error.value.codes == ["invalid_path"]
    assert outside_path.read_bytes() == original_content


def test_replace_note_content__temporary_content_mismatch__raises_without_modifying_file(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = "pages/kubernetes.md"
    note_path = tmp_vault_path / path
    original_content = note_path.read_bytes()
    read_bytes = Path.read_bytes

    def read_with_temporary_mismatch(file_path: Path) -> bytes:
        if file_path == note_path:
            return read_bytes(file_path)
        return b"Unexpected temporary content"

    monkeypatch.setattr(Path, "read_bytes", read_with_temporary_mismatch)

    with pytest.raises(EditNoteError) as error:
        replace_note_content(tmp_vault_path, path, "# New content")

    assert error.value.codes == ["temporary_verification_failed"]
    assert note_path.read_bytes() == original_content


@pytest.mark.parametrize("failure_kind", ["content_mismatch", "read_error"])
def test_replace_note_content__final_verification_failure__raises_after_replacing_file(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch, failure_kind: str
):
    path = "pages/kubernetes.md"
    note_path = tmp_vault_path / path
    content = "# New content"
    expected_content = content.encode("utf-8")
    read_bytes = Path.read_bytes

    def read_with_final_failure(file_path: Path) -> bytes:
        actual_content = read_bytes(file_path)
        if file_path == note_path and actual_content == expected_content:
            if failure_kind == "read_error":
                raise OSError("Simulated final read failure")
            return b"Unexpected final content"
        return actual_content

    monkeypatch.setattr(Path, "read_bytes", read_with_final_failure)

    with pytest.raises(EditNoteError) as error:
        replace_note_content(tmp_vault_path, path, content)

    assert error.value.codes == ["final_verification_failed"]
    assert read_bytes(note_path) == expected_content


@pytest.mark.parametrize("failure_stage", ["validation", "replacement"])
@pytest.mark.parametrize(
    ("failure", "expected_code"),
    [
        pytest.param(
            PermissionError("Simulated permission failure"),
            "permission_denied",
            id="permission_denied",
        ),
        pytest.param(
            OSError("Simulated file operation failure"),
            "file_operation_failed",
            id="file_operation_failed",
        ),
    ],
)
def test_replace_note_content__file_operation_error__raises_without_modifying_file(
    tmp_vault_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: OSError,
    expected_code: str,
    failure_stage: str,
):
    path = "pages/kubernetes.md"
    note_path = tmp_vault_path / path
    original_content = note_path.read_bytes()
    original_files = set(note_path.parent.iterdir())

    def fail_replace(file_path: Path, target: Path) -> Path:
        raise failure

    is_symlink = Path.is_symlink

    def fail_validation(file_path: Path) -> bool:
        if file_path == note_path:
            raise failure
        return is_symlink(file_path)

    if failure_stage == "validation":
        monkeypatch.setattr(Path, "is_symlink", fail_validation)
    else:
        monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(EditNoteError) as error:
        replace_note_content(tmp_vault_path, path, "# New content")

    assert error.value.codes == [expected_code]
    assert note_path.read_bytes() == original_content
    assert set(note_path.parent.iterdir()) == original_files


def test_replace_note_content__operation_and_cleanup_fail__raises_with_both_error_codes(
    tmp_vault_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = "pages/kubernetes.md"
    note_path = tmp_vault_path / path
    original_content = note_path.read_bytes()

    def fail_replace(file_path: Path, target: Path) -> Path:
        raise PermissionError("Simulated replacement failure")

    def fail_unlink(file_path: Path, missing_ok: bool = False) -> None:
        raise PermissionError("Simulated cleanup failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    monkeypatch.setattr(Path, "unlink", fail_unlink)

    with pytest.raises(EditNoteError) as error:
        replace_note_content(tmp_vault_path, path, "# New content")

    assert error.value.codes == ["permission_denied", "temporary_cleanup_failed"]
    assert note_path.read_bytes() == original_content


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
        "app.tools.edit_note.replace_note_content", fail_replace_note_content
    )
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_vault_path))
    monkeypatch.chdir(tmp_vault_path)
    get_settings.cache_clear()

    try:
        result = edit_note(path, "# New content")
    finally:
        get_settings.cache_clear()

    assert result == EditNoteFailure(ok=False, path=path, error=error_codes)
