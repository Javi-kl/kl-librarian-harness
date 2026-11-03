from pathlib import Path


class NotePathError(Exception):
    """Comunica el motivo por el que una ruta de nota no es válida."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def resolve_note_path(vault_path: Path, path: str) -> Path:
    """Valida una ruta relativa sin enlaces y devuelve el archivo .md existente."""
    relative_path = Path(path)
    if relative_path.is_absolute():
        raise NotePathError("invalid_path")
    if ".." in relative_path.parts:
        raise NotePathError("invalid_path")

    note_path = vault_path.resolve()
    for part in relative_path.parts:
        note_path = note_path / part
        if note_path.is_symlink():
            raise NotePathError("invalid_path")

    if not note_path.exists():
        raise NotePathError("note_not_found")
    if not note_path.is_file() or note_path.suffix != ".md":
        raise NotePathError("invalid_path")
    return note_path
