from pathlib import Path

import pytest

from app.tools.edit_note import replace_note_content


def test_replace_note_content__existing_note__replaces_full_content(
    tmp_vault_path: Path,
):
    path = "pages/kubernetes.md"
    content = "# Kubernetes\nContenido nuevo."

    replace_note_content(tmp_vault_path, path, content)

    assert (tmp_vault_path / path).read_bytes() == content.encode("utf-8")


def test_replace_note_content__missing_note__raises_without_creating_file(
    tmp_vault_path: Path,
):
    path = "pages/missing.md"

    with pytest.raises(FileNotFoundError):
        replace_note_content(tmp_vault_path, path, "# New content")

    assert not (tmp_vault_path / path).exists()
