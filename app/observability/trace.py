import json
import logging

from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def write_trace_event(
    trace_path: Path,
    event: dict[str, object],
) -> None:
    """Añade un evento JSONL y propaga los errores de serialización o escritura."""
    line = json.dumps(event, ensure_ascii=False, allow_nan=False)
    with trace_path.open("a", encoding="utf-8", newline="\n") as trace_file:
        trace_file.write(line + "\n")


def record_decision(
    trace_path: Path,
    *,
    conversation_id: str,
    call_id: str,
    tool_name: str,
    note_path: str,
    decision: str,
) -> None:
    """Registra una decisión; avisa sin interrumpir ante fallos de escritura o codificación."""
    try:
        write_trace_event(
            trace_path,
            {
                "event": "decision",
                "timestamp": datetime.now(UTC).isoformat(),
                "conversation_id": conversation_id,
                "call_id": call_id,
                "tool": tool_name,
                "path": note_path,
                "decision": decision,
            },
        )
    except (OSError, UnicodeError) as error:
        logger.warning(
            "No se pudo registrar la decisión de %s sobre %s (llamada %s). "
            "La traza puede quedar incompleta: %s",
            tool_name,
            note_path,
            call_id,
            error,
        )
