from pathlib import Path

import pytest

from app.tools.delete_note import DeleteNoteError, move_note_to_trash


def test_move_note_to_trash__existing_note__moves_file_and_returns_relative_path(
    tmp_vault_path: Path,
):
    path = "pages/kubernetes.md"
    original_content = (tmp_vault_path / path).read_bytes()

    trash_path = move_note_to_trash(tmp_vault_path, path)

    assert trash_path == "trash/kubernetes.md.trash"
    assert not (tmp_vault_path / path).exists()
    assert (tmp_vault_path / trash_path).read_bytes() == original_content


def test_move_note_to_trash__symlink_trash__rejects_without_moving_note(
    tmp_path: Path,
):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    note_path = vault_path / "note.md"
    original_content = b"Original content"
    note_path.write_bytes(original_content)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (vault_path / "trash").symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(DeleteNoteError) as error:
        move_note_to_trash(vault_path, "note.md")

    assert error.value.codes == ["invalid_path"]
    assert note_path.read_bytes() == original_content
    assert list(outside_dir.iterdir()) == []


def test_move_note_to_trash__missing_note__raises_without_creating_trash(
    tmp_vault_path: Path,
):
    path = "pages/missing.md"

    with pytest.raises(DeleteNoteError) as error:
        move_note_to_trash(tmp_vault_path, path)

    assert error.value.codes == ["note_not_found"]
    assert not (tmp_vault_path / "trash").exists()


@pytest.mark.parametrize("target_kind", ["non_markdown_file", "directory"])
def test_move_note_to_trash__invalid_target__raises_without_moving_file(
    tmp_vault_path: Path, target_kind: str
):
    path = (
        "pages/settings.txt"
        if target_kind == "non_markdown_file"
        else "pages/folder.md"
    )
    target_path = tmp_vault_path / path
    original_content = b"Original settings"
    if target_kind == "directory":
        target_path.mkdir()
    else:
        target_path.write_bytes(original_content)

    with pytest.raises(DeleteNoteError) as error:
        move_note_to_trash(tmp_vault_path, path)

    assert error.value.codes == ["invalid_path"]
    if target_kind == "directory":
        assert target_path.is_dir()
    else:
        assert target_path.read_bytes() == original_content


@pytest.mark.parametrize("path_kind", ["absolute", "parent_segment", "symlink"])
def test_move_note_to_trash__forbidden_path__raises_without_moving_file(
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

    with pytest.raises(DeleteNoteError) as error:
        move_note_to_trash(vault_path, paths[path_kind])

    assert error.value.codes == ["invalid_path"]
    assert outside_path.read_bytes() == original_content
    assert not (vault_path / "trash").exists()


def test_move_note_to_trash__note_already_in_trash__keeps_both_versions(
    tmp_vault_path: Path,
):
    path = "pages/kubernetes.md"
    first_content = (tmp_vault_path / path).read_text(encoding="utf-8")

    first_trash_path = move_note_to_trash(tmp_vault_path, path)
    (tmp_vault_path / path).write_text(
        "# Kubernetes\nVersion recreada.", encoding="utf-8"
    )
    second_trash_path = move_note_to_trash(tmp_vault_path, path)

    assert first_trash_path == "trash/kubernetes.md.trash"
    assert second_trash_path == "trash/kubernetes.1.md.trash"
    assert (tmp_vault_path / first_trash_path).read_text(
        encoding="utf-8"
    ) == first_content
    assert not (tmp_vault_path / path).exists()


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
def test_move_note_to_trash__rename_fails__raises_with_mapped_error_code(
    tmp_vault_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: OSError,
    expected_code: str,
):
    path = "pages/kubernetes.md"

    def fail_rename(file_path: Path, target: Path) -> Path:
        raise failure

    monkeypatch.setattr(Path, "rename", fail_rename)

    with pytest.raises(DeleteNoteError) as error:
        move_note_to_trash(tmp_vault_path, path)

    assert error.value.codes == [expected_code]
    assert (tmp_vault_path / path).exists()
