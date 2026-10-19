from pathlib import Path

from app.shared.config import get_settings
from app.tools.schemas import DeleteNoteFailure, DeleteNoteSuccess

TRASH_DIR_NAME = "trash"
TRASH_SUFFIX = ".md.trash"


class DeleteNoteError(Exception):
    """Comunica los fallos previstos de un borrado, en orden de prioridad."""

    def __init__(self, codes: list[str]) -> None:
        self.codes = codes
        super().__init__(*codes)


# Copia de la validación de edit_note a propósito: son reglas de seguridad y
# preferimos tenerlas a la vista en cada tool antes que acoplarlas por un
# refactor. Extraer a un módulo compartido cuando una tercera tool las pida.
def _resolve_note_path(vault_path: Path, path: str) -> Path:
    """Valida las restricciones de la ruta y devuelve la nota a borrar."""
    relative_path = Path(path)
    if relative_path.is_absolute():
        raise DeleteNoteError(["invalid_path"])
    if ".." in relative_path.parts:
        raise DeleteNoteError(["invalid_path"])

    note_path = vault_path.resolve()
    for part in relative_path.parts:
        note_path = note_path / part
        if note_path.is_symlink():
            raise DeleteNoteError(["invalid_path"])

    if not note_path.exists():
        raise DeleteNoteError(["note_not_found"])
    if not note_path.is_file() or note_path.suffix != ".md":
        raise DeleteNoteError(["invalid_path"])
    return note_path


def _available_trash_path(trash_dir: Path, note_path: Path) -> Path:
    """Devuelve un destino libre en trash, con contador si el nombre ya existe."""
    trash_path = trash_dir / f"{note_path.stem}{TRASH_SUFFIX}"
    counter = 1
    while trash_path.exists():
        trash_path = trash_dir / f"{note_path.stem}.{counter}{TRASH_SUFFIX}"
        counter += 1
    return trash_path


def move_note_to_trash(vault_path: Path, path: str) -> str:
    """Mueve una nota a vault/trash/ y devuelve su ruta relativa al vault."""
    try:
        note_path = _resolve_note_path(vault_path, path)
        trash_dir = vault_path / TRASH_DIR_NAME
        if trash_dir.is_symlink():
            raise DeleteNoteError(["invalid_path"])
        trash_dir.mkdir(exist_ok=True)
        trash_path = _available_trash_path(trash_dir, note_path)
        note_path.rename(trash_path)
        return str(trash_path.relative_to(vault_path))
    except PermissionError as error:
        raise DeleteNoteError(["permission_denied"]) from error
    except OSError as error:
        raise DeleteNoteError(["file_operation_failed"]) from error


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
