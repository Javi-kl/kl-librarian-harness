from pathlib import Path

import pytest


@pytest.fixture
def tmp_vault_path(tmp_path: Path) -> Path:
    """Una subcarpeta y dos notas conocidas."""
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "podman.md").write_text("# Podman\nContenedores.", encoding="utf-8")
    (pages / "kubernetes.md").write_text(
        "# Kubernetes\nOrquestador de contenedores.", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def tmp_vault_path_with_16_notes(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()

    for n in range(1, 17):
        (pages / f"nota{n}.md").write_text("contenedor " * n, encoding="utf-8")

    return tmp_path
