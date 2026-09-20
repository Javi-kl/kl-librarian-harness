from pathlib import Path

from app.shared.config import get_settings
from app.tools.schemas import NoteHit

MAX_NOTES_LENGTH = 15


def find_hits(vault_path: Path, terms: list[str], limit: int) -> list[NoteHit]:
    """
    Primero hits descendente (el -), y en empate, path ascendente.
    Coincidencia = palabra/frase completa.
    """
    # ej: sorted(notes, key=lambda n: (-n.hits, n.path)) TODO REPASAR COMPRENSION.
    # TODO Limpiar duplicados en el input 'terms' después de normalizar.
    # TODO Buscamos por límite de palabra (\b)regex
    raise NotImplementedError


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
