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
