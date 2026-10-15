from pathlib import Path

from app.tools.schemas import EditNoteFailure, EditNoteSuccess


def replace_note_content(vault_path: Path, path: str, content: str) -> int:
    """Reemplaza una nota y devuelve el tamaño verificado; los fallos son excepciones."""
    note_path = vault_path / path
    if not note_path.exists():
        raise FileNotFoundError(note_path)
    return note_path.write_bytes(content.encode("utf-8"))


def edit_note(path: str, content: str) -> EditNoteSuccess | EditNoteFailure:
    """
    Reemplaza todo el contenido de una nota Markdown existente dentro del vault.

    Úsala para modificar una nota, no para crearla, borrarla ni moverla.

    Args:
        path: Ruta relativa a la raíz del vault, como "pages/kubernetes.md".
            Debe señalar un archivo .md existente. No se admiten rutas absolutas,
            segmentos ".." ni enlaces simbólicos en la ruta dentro del vault.
        content: Texto final completo que debe tener la nota, no un fragmento
            ni un diff. Incluye todo el contenido que deba conservarse.
            Se escribe en UTF-8, sin transformar saltos de línea ni añadir
            un salto final. Una cadena vacía deja el archivo vacío, sin borrarlo.

    Si el archivo ya contiene exactamente el texto solicitado, no se reescribe.
    Cuando hay cambios, comprueba el contenido antes de sustituir la nota
    y confirma el resultado leyendo el archivo final.

    Devuelve:
        Éxito: {ok: true, path, verified: true, bytes}.
            verified confirma que los bytes comprobados coinciden exactamente
            con el contenido solicitado en UTF-8 en el momento de verificarlos.
            bytes es el tamaño de los datos releídos y verificados.
        Fallo: {ok: false, path, error: [códigos]}.
            El primer código identifica el fallo principal. Si también falla
            la limpieza del archivo temporal, se añade su código después.

    Un fallo de verificación final significa que la nota ya fue sustituida,
    pero no pudo confirmarse su contenido. No se restaura automáticamente
    el contenido anterior.

    La aprobación y el control de lectura previa corresponden a los guardrails;
    esta función no concede autorización para escribir.
    """
    raise NotImplementedError
