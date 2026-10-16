import sys

from pathlib import Path
from tempfile import NamedTemporaryFile

from app.shared.config import get_settings
from app.tools.schemas import EditNoteFailure, EditNoteSuccess


class EditNoteError(Exception):
    """Comunica los fallos previstos de una edicion, en orden de prioridad."""

    def __init__(self, codes: list[str]) -> None:
        self.codes = codes
        super().__init__(*codes)


def _cleanup_temporary(
    temporary_path: Path, operation_error: BaseException | None
) -> None:
    """Elimina el temporal sin ocultar un fallo anterior de la operacion."""
    try:
        temporary_path.unlink(missing_ok=True)
    except OSError as cleanup_error:
        if isinstance(operation_error, EditNoteError):
            raise EditNoteError(
                [*operation_error.codes, "temporary_cleanup_failed"]
            ) from cleanup_error
        if operation_error is not None:
            operation_error.add_note(
                f"No se pudo eliminar el temporal {temporary_path}: {cleanup_error}"
            )
        else:
            raise EditNoteError(["temporary_cleanup_failed"]) from cleanup_error


def _resolve_note_path(vault_path: Path, path: str) -> Path:
    """Valida las restricciones de la ruta y devuelve el destino de la nota."""
    relative_path = Path(path)
    if relative_path.is_absolute():
        raise EditNoteError(["invalid_path"])
    if ".." in relative_path.parts:
        raise EditNoteError(["invalid_path"])

    note_path = vault_path.resolve()
    for part in relative_path.parts:
        note_path = note_path / part
        if note_path.is_symlink():
            raise EditNoteError(["invalid_path"])

    if not note_path.exists():
        raise EditNoteError(["note_not_found"])
    if not note_path.is_file() or note_path.suffix != ".md":
        raise EditNoteError(["invalid_path"])
    return note_path


def replace_note_content(vault_path: Path, path: str, content: str) -> int:
    """Reemplaza una nota y devuelve el tamaño verificado; señala fallos con EditNoteError."""
    expected_content = content.encode("utf-8")
    temporary_path: Path | None = None
    try:
        note_path = _resolve_note_path(vault_path, path)
        with NamedTemporaryFile(
            dir=note_path.parent, suffix=".tmp", delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(expected_content)

        prepared_content = temporary_path.read_bytes()
        if prepared_content != expected_content:
            raise EditNoteError(["temporary_verification_failed"])

        temporary_path.chmod(note_path.stat().st_mode & 0o777)
        temporary_path.replace(note_path)

        try:
            final_content = note_path.read_bytes()
        except OSError as error:
            raise EditNoteError(["final_verification_failed"]) from error
        if final_content != expected_content:
            raise EditNoteError(["final_verification_failed"])
        return len(final_content)
    except PermissionError as error:
        raise EditNoteError(["permission_denied"]) from error
    except OSError as error:
        raise EditNoteError(["file_operation_failed"]) from error
    finally:
        if temporary_path is not None:
            _cleanup_temporary(temporary_path, sys.exception())


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
