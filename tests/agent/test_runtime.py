from pathlib import Path
import pytest

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

from app.guardrails.state import ConversationState
from app.agent.runtime import create_agent
from app.shared.config import get_settings
from app.tools.schemas import NoteHit


def test_create_agent__initial_configuration__exposes_search_and_edit_tools():
    model = TestModel(call_tools=[])
    agent = create_agent(model)

    agent.run_sync(
        "Busca notas sobre Ollama.",
        deps=ConversationState(),
    )

    parameters = model.last_model_request_parameters
    assert parameters is not None
    assert [tool.name for tool in parameters.function_tools] == [
        "search_text",
        "edit_note",
    ]
    tool = parameters.function_tools[0]
    assert set(tool.parameters_json_schema["properties"]) == {"terms"}


def test_create_agent__search_requested__returns_matching_note_to_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    note_content = "# Ollama\nEjecuta modelos localmente."
    (tmp_path / "ollama.md").write_text(note_content, encoding="utf-8")

    (tmp_path / "gardening.md").write_text(
        "# Jardinería\nCuidados del romero.",
        encoding="utf-8",
    )
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_path))
    get_settings.cache_clear()

    def simulated_model(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        latest_message = messages[-1]
        assert isinstance(latest_message, ModelRequest)

        tool_returns = [
            part for part in latest_message.parts if isinstance(part, ToolReturnPart)
        ]

        if not tool_returns:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="search_text",
                        args={"terms": ["ollama"]},
                        tool_call_id="search-1",
                    )
                ]
            )
        tool_return = tool_returns[0]
        assert tool_return.tool_name == "search_text"
        assert tool_return.tool_call_id == "search-1"
        assert tool_return.content == [
            NoteHit(path="ollama.md", title="ollama", content=note_content, hits=1)
        ]

        return ModelResponse(parts=[TextPart("Fin de la simulación.")])

    agent = create_agent(FunctionModel(simulated_model))
    state = ConversationState()

    try:
        agent.run_sync(
            "Busca notas sobre Ollama.",
            deps=state,
            usage_limits=UsageLimits(request_limit=2),
        )
    finally:
        get_settings.cache_clear()

    assert state.read_notes == {"ollama.md": note_content}


def test_create_agent__edit_requested__defers_call_without_changing_note(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    tmp_note = vault_path / "gardening.md"

    content = b"cuidados del romero"
    tmp_note.write_bytes(content)
    monkeypatch.setenv("KB_VAULT_PATH", str(vault_path))
    get_settings.cache_clear()

    def simulated_model(
        messages: list[ModelMessage],
        info: AgentInfo,
    ) -> ModelResponse:
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="edit_note",
                    args={
                        "path": "gardening.md",
                        "content": "Contenido nuevo.",
                    },
                    tool_call_id="edit-1",
                )
            ]
        )

    agent = create_agent(FunctionModel(simulated_model))

    try:
        result = agent.run_sync(
            "Cambia la nota de jardinería.",
            deps=ConversationState(),
            usage_limits=UsageLimits(request_limit=1),
        )
    finally:
        get_settings.cache_clear()

    assert isinstance(result.output, DeferredToolRequests)
    assert len(result.output.approvals) == 1

    pending_call = result.output.approvals[0]
    assert pending_call.tool_name == "edit_note"
    assert pending_call.tool_call_id == "edit-1"
    assert pending_call.args_as_dict() == {
        "path": "gardening.md",
        "content": "Contenido nuevo.",
    }
    assert tmp_note.read_bytes() == content
