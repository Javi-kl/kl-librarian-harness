import json
import logging

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.observability.trace import record_decision, write_trace_event


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


def test_record_decision__valid_decision__writes_identified_event_with_utc_timestamp(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "operations.jsonl"

    record_decision(
        trace_path,
        conversation_id="conversation-1",
        call_id="edit-1",
        tool_name="edit_note",
        note_path="Ollama.md",
        decision="approved",
    )

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert datetime.fromisoformat(event.pop("timestamp")).tzinfo == UTC
    assert event == {
        "event": "decision",
        "conversation_id": "conversation-1",
        "call_id": "edit-1",
        "tool": "edit_note",
        "path": "Ollama.md",
        "decision": "approved",
    }


def test_record_decision__trace_not_writable__warns_without_raising(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="app.observability.trace")

    record_decision(
        tmp_path,
        conversation_id="conversation-1",
        call_id="edit-1",
        tool_name="edit_note",
        note_path="Ollama.md",
        decision="approved",
    )

    assert any(
        record.name == "app.observability.trace" and record.levelno == logging.WARNING
        for record in caplog.records
    )
