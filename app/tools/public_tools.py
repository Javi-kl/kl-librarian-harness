from pydantic_ai import RunContext

from app.shared.config import get_settings
from app.tools.delete_note import DeleteNoteError, move_note_to_trash
from app.tools.edit_note import EditNoteError, replace_note_content
from app.tools.schemas import (
    DeleteNoteFailure,
    DeleteNoteSuccess,
    EditNoteFailure,
    EditNoteSuccess,
    NoteHit,
)
from app.guardrails.state import ConversationState
from app.tools.search_text import MAX_NOTES_LENGTH, find_hits


def search_text(ctx: RunContext[ConversationState], terms: list[str]) -> list[NoteHit]:
    """
    Busca texto en notas .md del vault y sus subcarpetas.
    Ignora archivos y carpetas que sean enlaces simbólicos.
    Devuelve notas que contengan al menos uno de los términos.

    Args:
        terms: Términos o frases literales. Ignora mayúsculas y acentos,
            pero distingue ñ de n. Una coincidencia no puede tener letras,
            números o "_" inmediatamente antes o después:
            "C++" coincide en "(C++)", pero no en "C++17".
            No expande variantes: incluye "casa" y "casas" si necesitas ambas.

    Returns:
        list[NoteHit]: Hasta 15 notas; [] sin coincidencias. Orden por hits
            descendente y path ascendente en empates.
            path: ruta relativa al vault; title: nombre sin extensión;
            content: texto completo sin normalizar;
            hits: suma de apariciones de los términos normalizados distintos.
    """
    notes = find_hits(get_settings().KB_VAULT_PATH, terms, MAX_NOTES_LENGTH)
    for note in notes:
        ctx.deps.read_notes[note.path] = note.content

    return notes


def edit_note(path: str, content: str) -> EditNoteSuccess | EditNoteFailure:
    """
    Reemplaza todo el texto de una nota Markdown existente.
    No crea, borra ni mueve notas.

    Args:
        path: Ruta relativa al vault, como "pages/kubernetes.md".
            Archivo .md existente, sin segmentos ".." ni enlaces simbólicos
            en la nota o sus carpetas dentro del vault.
        content: Texto final completo, no un fragmento ni un diff. Incluye
            todo lo que deba conservarse. Se escribe en UTF-8 sin transformar
            saltos de línea ni añadir uno final. "" deja el archivo vacío.

    Returns:
        EditNoteSuccess | EditNoteFailure: Resultado de la edición.
            Éxito: {ok: true, path, verified: true, bytes}.
            verified confirma coincidencia exacta con el texto solicitado
            al releer la nota final; bytes es su tamaño en bytes.
            Fallo: {ok: false, path, error: [códigos]}.
            Primero aparece el fallo principal; después, el de limpieza si ocurre.
            note_not_found: la nota no existe al comenzar.
            invalid_path: ruta absoluta, con "..", con enlaces o destino
                que no es un archivo .md.
            permission_denied: el sistema deniega una operación por permisos.
            file_operation_failed: otro fallo de operación con archivos.
            temporary_verification_failed: contenido preparado distinto;
                no se sustituye la original.
            final_verification_failed: nota sustituida, pero no se pudo leer
                o no coincide con lo solicitado; no se restaura automáticamente.
            temporary_cleanup_failed: no se pudo eliminar el temporal.
            Una respuesta de fallo no garantiza que la nota siga intacta.
    """
    vault_path = get_settings().KB_VAULT_PATH
    try:
        size = replace_note_content(vault_path, path, content)
    except EditNoteError as error:
        return EditNoteFailure(ok=False, path=path, error=error.codes)
    return EditNoteSuccess(ok=True, path=path, verified=True, bytes=size)


def delete_note(path: str) -> DeleteNoteSuccess | DeleteNoteFailure:
    """
    Mueve una nota Markdown a la papelera del vault; no la borra en firme.

    Args:
        path: Ruta relativa al vault, como "pages/kubernetes.md".
            Archivo .md existente, sin segmentos ".." ni enlaces simbólicos
            en la nota o sus carpetas dentro del vault.

    Returns:
        DeleteNoteSuccess | DeleteNoteFailure: Resultado del borrado.
            Éxito: {ok: true, path, trash_path}.
            trash_path: ruta relativa al vault donde queda la nota, con el
                mismo nombre más ".trash" ("trash/kubernetes.md.trash").
                Si ese nombre ya estaba ocupado por un borrado anterior,
                se añade un contador (".1", ".2"...).
                Renombrar el fichero de vuelta a ".md" recupera la nota.
            Fallo: {ok: false, path, error: [códigos]}.
            note_not_found: la nota no existe al comenzar.
            invalid_path: ruta absoluta, con "..", con enlaces o destino
                que no es un archivo .md; también si la papelera es un
                enlace simbólico.
            permission_denied: el sistema deniega una operación por permisos.
            file_operation_failed: otro fallo de operación con archivos.
            Si la validación falla, la nota no se mueve.
    """
    vault_path = get_settings().KB_VAULT_PATH
    try:
        trash_path = move_note_to_trash(vault_path, path)
    except DeleteNoteError as error:
        return DeleteNoteFailure(ok=False, path=path, error=error.codes)
    return DeleteNoteSuccess(ok=True, path=path, trash_path=trash_path)
