import re

from pathlib import Path

from app.shared.config import get_settings
from app.tools.schemas import NoteHit

MAX_NOTES_LENGTH = 15


# TODO TDD Quitar acentos.
def _normalize_page_content(content: str) -> str:
    return content.lower()


def _normalize_terms(terms: list[str]) -> list[str]:
    normalized_terms = [term.lower() for term in terms]
    return list(set(normalized_terms))


def _count_word_hits(content: str, term: str) -> int:
    pattern = r"\b" + re.escape(term) + r"\b"
    return len(re.findall(pattern, content))


def find_hits(vault_path: Path, terms: list[str], limit: int) -> list[NoteHit]:
    """
    Primero hits descendente (el -), y en empate, path ascendente.
    Coincidencia = palabra/frase completa.
    """
    # TODO TDD Limpiar duplicados en el input 'terms' después de normalizar.
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
    Busca en el vault notas que contengan alguno de los términos dados.
    Úsala para localizar contenido.
    terms=lista de palabras o frases cortas, una nota entra si contiene al menos uno.
    Además los términos coinciden como palabras/frases completas: no se detectan plurales
    ni variantes. Si las necesitas, inclúyelas tú en la lista(p. ej. casa, casas).
    Siempre devuelve lista, si no hay coincidencias, [].
    Ordenada por hits descendente, maximo 15 notas.
    path=relativo a la raíz del vault,
    title=nombre del archivo sin extensión, content=text completo,
    hits=suma de apariciones de todos los términos, ignorando mayúsculas y acentos.
    """
    return find_hits(get_settings().KB_VAULT_PATH, terms, MAX_NOTES_LENGTH)
