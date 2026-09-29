from pathlib import Path

from app.tools.schemas import NoteHit
from app.tools.search_text import find_hits


def test_find_hits__no_matches__returns_empty_list(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["inexistente"], limit=15)
    assert notes == []


def test_find_hits__term_once__counts_one_hit(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["kubernetes"], limit=15)
    assert notes == [
        NoteHit(
            path="pages/kubernetes.md",
            title="kubernetes",
            content="# Kubernetes\nOrquestador de contenedores.",
            hits=1,
        )
    ]


def test_find_hits__multiple_notes_with_different_hits__orders_by_hits_desc(
    tmp_vault_path: Path,
):
    notes = find_hits(
        tmp_vault_path,
        ["kubernetes", "podman", "contenedores", "orquestador"],
        limit=15,
    )
    assert notes == [
        NoteHit(
            path="pages/kubernetes.md",
            title="kubernetes",
            content="# Kubernetes\nOrquestador de contenedores.",
            hits=3,
        ),
        NoteHit(
            path="pages/podman.md",
            title="podman",
            content="# Podman\nContenedores.",
            hits=2,
        ),
    ]


def test_find_hits__more_than_15_notes__returns_top_15_sorted_by_hits(
    tmp_vault_path_with_16_notes: Path,
):
    notes = find_hits(tmp_vault_path_with_16_notes, ["contenedor"], limit=15)
    expected = [
        NoteHit(
            path=f"pages/nota{k}.md",
            title=f"nota{k}",
            content="contenedor " * k,
            hits=k,
        )
        for k in range(16, 1, -1)
    ]
    assert notes == expected


def test_find_hits__equal_hits__returns_sorted_by_path_asc(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["contenedores"], limit=15)
    assert notes == [
        NoteHit(
            path="pages/kubernetes.md",
            title="kubernetes",
            content="# Kubernetes\nOrquestador de contenedores.",
            hits=1,
        ),
        NoteHit(
            path="pages/podman.md",
            title="podman",
            content="# Podman\nContenedores.",
            hits=1,
        ),
    ]
