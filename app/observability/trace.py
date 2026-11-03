import json

from datetime import UTC, datetime
from pathlib import Path


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
    """Registra una decisión con fecha UTC y propaga los errores de escritura."""
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
