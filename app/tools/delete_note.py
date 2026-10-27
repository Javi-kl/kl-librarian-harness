from pathlib import Path

from app.shared.note_paths import NotePathError, resolve_note_path

TRASH_DIR_NAME = "trash"
TRASH_SUFFIX = ".md.trash"


class DeleteNoteError(Exception):
    """Comunica los fallos previstos de un borrado, en orden de prioridad."""

    def __init__(self, codes: list[str]) -> None:
        self.codes = codes
        super().__init__(*codes)


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
        note_path = resolve_note_path(vault_path, path)
        trash_dir = vault_path / TRASH_DIR_NAME
        if trash_dir.is_symlink():
            raise DeleteNoteError(["invalid_path"])
        trash_dir.mkdir(exist_ok=True)
        trash_path = _available_trash_path(trash_dir, note_path)
        note_path.rename(trash_path)
        return str(trash_path.relative_to(vault_path))
    except NotePathError as error:
        raise DeleteNoteError([error.code]) from error
    except PermissionError as error:
        raise DeleteNoteError(["permission_denied"]) from error
    except OSError as error:
        raise DeleteNoteError(["file_operation_failed"]) from error
