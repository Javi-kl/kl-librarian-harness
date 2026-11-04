import logging
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic_ai.messages import ToolCallPart

from app.cli import review
from app.guardrails.approval import EditProposal
from app.guardrails.state import ConversationState


@pytest.mark.parametrize(
    ("answer", "expected_decision"),
    [("s", "approved"), ("n", "rejected")],
)
def test_review_proposal__user_answer__shows_diff_and_returns_decision(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    answer: str,
    expected_decision: str,
) -> None:
    proposal = EditProposal(
        path="ollama.md",
        original_bytes=b"Original\n",
        content="Propuesto\n",
        diff="-Original\n+Propuesto\n",
    )
    user_input = Mock(return_value=answer)
    monkeypatch.setattr("builtins.input", user_input)
    caplog.set_level(logging.INFO, logger="app.cli.review")

    decision = review.review_proposal(proposal)

    assert decision == expected_decision
    assert proposal.diff in caplog.text
    user_input.assert_called_once()
    assert proposal.path in user_input.call_args.args[0]


@pytest.mark.parametrize("decision", ["approved", "rejected"])
def test_review_pending_operations__user_decision__records_and_respects_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    decision: str,
) -> None:
    """Sustituye guardrails, presentación y registro para comprobar la coordinación
    de revisión, sin ejecutar el agente, acceder al vault ni escribir la traza."""
    proposal = EditProposal(
        path="ollama.md",
        original_bytes=b"Original\n",
        content="Propuesto\n",
        diff="-Original\n+Propuesto\n",
    )
    prepare = Mock(return_value=proposal)
    recorder = Mock()
    validator = Mock()
    monkeypatch.setattr(review, "prepare_edit_for_approval", prepare)
    monkeypatch.setattr(review, "review_proposal", Mock(return_value=decision))
    monkeypatch.setattr(review, "record_decision", recorder)
    monkeypatch.setattr(review, "validate_proposals_unchanged", validator)
    call = ToolCallPart(
        tool_name="edit_note",
        args={"path": proposal.path, "content": proposal.content},
        tool_call_id="edit-1",
    )
    state = ConversationState()
    trace_path = tmp_path / "operations.jsonl"

    accepted = review.review_pending_operations(
        [call],
        vault_path=tmp_path,
        trace_path=trace_path,
        state=state,
        conversation_id="conversation-1",
    )

    prepare.assert_called_once_with(
        vault_path=tmp_path, state=state, path=proposal.path, content=proposal.content
    )
    recorder.assert_called_once_with(
        trace_path,
        conversation_id="conversation-1",
        call_id="edit-1",
        tool_name="edit_note",
        note_path=proposal.path,
        decision=decision,
    )
    if decision == "approved":
        assert accepted == {"edit-1": proposal}
        validator.assert_called_once()
        assert validator.call_args.args[0] == tmp_path
        assert list(validator.call_args.args[1]) == [proposal]
    else:
        assert accepted is None
        validator.assert_not_called()
