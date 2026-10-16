import re
import unicodedata

from pathlib import Path

from app.shared.config import get_settings
from app.tools.schemas import NoteHit

MAX_NOTES_LENGTH = 15


def _normalize_word_accents(words: str) -> str:
    break_down_words = unicodedata.normalize("NFD", words)
    return re.sub(r"[\u0300-\u036f]", "", break_down_words)


def _normalize_page_content(content: str) -> str:
    normalized_content = _normalize_word_accents(content)
    return normalized_content.lower()


# TODO Caso de la 'ñ'. Actualmente es transformada en 'n'
def _normalize_terms(terms: list[str]) -> list[str]:
    normalized_terms = {
        _normalize_word_accents(term.lower().strip()) for term in terms if term.strip()
    }
    return list(normalized_terms)


# TODO Comprobar si funciona bien con terminos como: 'C++'
def _count_word_hits(content: str, term: str) -> int:
    if term != "":
        pattern = r"\b" + re.escape(term) + r"\b"
        return len(re.findall(pattern, content))
    else:
        return 0


def find_hits(vault_path: Path, terms: list[str], limit: int) -> list[NoteHit]:
    """
    Primero hits descendente (el -), y en empate, path ascendente.
    Coincidencia = palabra/frase completa.
    """
    notes_list = []
    page_paths = vault_path.rglob("*.md")
    normalized_terms = _normalize_terms(terms)
    for page in page_paths:
        content = page.read_text()
        normalized_content = _normalize_page_content(content)

        hits = sum(
            _count_word_hits(normalized_content, term) for term in normalized_terms
        )

        if hits > 0:
            note = NoteHit(
                path=str(page.relative_to(vault_path)),
                title=page.stem,
                content=content,
                hits=hits,
            )
            notes_list.append(note)

    order_notes = sorted(notes_list, key=lambda n: (-n.hits, n.path))[:limit]
    return order_notes


def search_text(terms: list[str]) -> list[NoteHit]:
    """
    Busca texto en notas .md del vault y sus subcarpetas.

    Args:
        terms: Palabras/frases completas; basta una coincidencia. Ignora
            mayúsculas y acentos; no expande variantes (incluye "casa" y
            "casas" si necesitas ambas).

    Returns:
        list[NoteHit]: Hasta 15 notas; [] sin coincidencias. Orden por hits
            descendente y path ascendente en empates.
            path: ruta relativa al vault; title: nombre sin extensión;
            content: texto completo sin normalizar;
            hits: suma de apariciones de los términos normalizados distintos.
    """
    return find_hits(get_settings().KB_VAULT_PATH, terms, MAX_NOTES_LENGTH)
