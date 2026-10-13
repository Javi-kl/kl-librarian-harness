from pathlib import Path

import pytest


@pytest.fixture
def tmp_vault_path(tmp_path: Path) -> Path:
    """Una subcarpeta y 3 notas conocidas."""
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "podman.md").write_text("# Podman\nContenedores.", encoding="utf-8")
    (pages / "kubernetes.md").write_text(
        "# Kubernetes\nOrquestador de contenedores.", encoding="utf-8"
    )
    (pages / "linux.md").write_text(
        "# Linux\nComo hacer una búsqueda con grep.", encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def tmp_vault_path_with_16_notes(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()

    for n in range(1, 17):
        (pages / f"nota{n}.md").write_text("contenedor " * n, encoding="utf-8")

    return tmp_path


@pytest.fixture
def tmp_no_ascii_vault_path(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "japones.md").write_text("# Japones\n日本", encoding="utf-8")

    return tmp_path
