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


def test_find_hits__equal_hits__returns_sorted_by_path_asc(
    tmp_vault_path: Path,
):
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


def test_find_hits__term_is_substring_of_word__counts_only_exact_matches(
    tmp_vault_path: Path,
):
    notes = find_hits(tmp_vault_path, ["contenedor"], limit=15)
    assert notes == []


def test_find_hits__multi_word_term__counts_phrase_occurrences(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["de contenedores", "orquestador de"], limit=15)

    assert notes == [
        NoteHit(
            path="pages/kubernetes.md",
            title="kubernetes",
            content="# Kubernetes\nOrquestador de contenedores.",
            hits=2,
        )
    ]


def test_find_hits__phrase_almost_present__returns_empty_list(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["de contenedor"], limit=15)

    assert notes == []


def test_find_hits__duplicated_terms__counts_each_term_once(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["Orquestador", "orquestador"], limit=15)

    assert notes == [
        NoteHit(
            path="pages/kubernetes.md",
            title="kubernetes",
            content="# Kubernetes\nOrquestador de contenedores.",
            hits=1,
        )
    ]


def test_find_hits__term_without_accent__matches_accented_word(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["busqueda"], limit=15)

    assert notes == [
        NoteHit(
            path="pages/linux.md",
            title="linux",
            content="# Linux\nComo hacer una búsqueda con grep.",
            hits=1,
        )
    ]


def test_find_hits__term_with_accent__matches_word_without_accent(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["cómo"], limit=15)

    assert notes == [
        NoteHit(
            path="pages/linux.md",
            title="linux",
            content="# Linux\nComo hacer una búsqueda con grep.",
            hits=1,
        )
    ]


def test_find_hits__non_ascii_term__matches_note_containing_it(
    tmp_no_ascii_vault_path: Path,
):
    notes = find_hits(tmp_no_ascii_vault_path, ["日本"], limit=15)

    assert notes == [
        NoteHit(
            path="pages/japones.md",
            title="japones",
            content="# Japones\n日本",
            hits=1,
        )
    ]


def test_find_hits__blank_terms__returns_empty_list(tmp_vault_path: Path):
    notes = find_hits(tmp_vault_path, ["", "   "], limit=15)

    assert notes == []


def test_find_hits__terms_with_symbols__counts_literal_matches(tmp_path: Path):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "lenguajes.md").write_text(
        "# lenguajes\nUso C++, C# y .NET.", encoding="utf-8"
    )
    notes = find_hits(tmp_path, ["C++", "C#", ".NET"], limit=15)

    assert notes == [
        NoteHit(
            path="vault/lenguajes.md",
            title="lenguajes",
            content="# lenguajes\nUso C++, C# y .NET.",
            hits=3,
        )
    ]


def test_find_hits__terms_inside_longer_names__returns_empty_list(tmp_path: Path):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "lenguajes.md").write_text(
        "# lenguajes\nUso C++17 y .NETCore.", encoding="utf-8"
    )
    notes = find_hits(tmp_path, ["C++", ".NET"], limit=15)

    assert notes == []


def test_find_hits__term_with_enye__does_not_match_plain_n(tmp_path: Path):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "cumpleaños.md").write_text(
        "# Cumpleaños\nano y año.", encoding="utf-8"
    )
    notes = find_hits(tmp_path, ["año"], limit=15)

    assert notes == [
        NoteHit(
            path="vault/cumpleaños.md",
            title="cumpleaños",
            content="# Cumpleaños\nano y año.",
            hits=1,
        )
    ]


def test_find_hits__decomposed_enye_in_content__matches_composed_term(tmp_path: Path):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "cumpleaños.md").write_text(
        "# Cumpleaños\nan\u0303o.", encoding="utf-8"
    )
    notes = find_hits(tmp_path, ["año"], limit=15)

    assert notes == [
        NoteHit(
            path="vault/cumpleaños.md",
            title="cumpleaños",
            content="# Cumpleaños\nan\u0303o.",
            hits=1,
        )
    ]
