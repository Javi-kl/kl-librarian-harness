import json

from pathlib import Path

from app.observability.trace import write_trace_event


def test_write_trace_event__two_events__appends_valid_json_lines_in_order(
    tmp_path: Path,
) -> None:

    trace_path = tmp_path / "operations.jsonl"
    decision: dict[str, object] = {
        "event": "decision",
        "call_id": "edit-1",
        "tool": "edit_note",
        "path": "Ollama.md",
        "decision": "approved",
    }
    result: dict[str, object] = {
        "event": "mutation_result",
        "call_id": "edit-1",
        "status": "succeeded",
    }
    write_trace_event(trace_path, decision)
    write_trace_event(trace_path, result)
    lines = trace_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert [json.loads(line) for line in lines] == [decision, result]
