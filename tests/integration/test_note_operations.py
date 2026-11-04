import pytest

from pathlib import Path
from pydantic_ai.messages import (
    ModelRequest,
    ToolCallPart,
    ToolReturnPart,
    ModelMessage,
    ModelResponse,
    TextPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.usage import UsageLimits

from app.agent.runtime import create_agent
from app.cli import chat as cli
from app.guardrails.state import ConversationState
from app.shared.config import get_settings
from app.tools.schemas import NoteHit


@pytest.mark.parametrize(
    ("answer", "external_content", "expected_content"),
    [
        pytest.param("s", None, b"# Ollama\nTexto actualizado.\n", id="approved"),
        pytest.param(
            "n", None, b"# Ollama\nEjecuta modelos localmente.\n", id="rejected"
        ),
        pytest.param(
            "s",
            b"# Ollama\nCambio manual del usuario.\n",
            b"# Ollama\nCambio manual del usuario.\n",
            id="changed_during_confirmation",
        ),
    ],
)
def test_run_chat__edit_reviewed_after_search__preserves_expected_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    answer: str,
    external_content: bytes | None,
    expected_content: bytes,
) -> None:
    """Simula búsqueda y revisión de una edición por CLI sobre una nota temporal.
    Aceptar escribe el contenido propuesto; rechazar o cambiar la nota durante
    la confirmación conserva el contenido que no debe sobrescribirse."""

    note_path = tmp_path / "ollama.md"
    original_content = b"# Ollama\nEjecuta modelos localmente.\n"
    note_path.write_bytes(original_content)

    def simulated_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        latest_message = messages[-1]
        assert isinstance(latest_message, ModelRequest)

        search_completed = any(
            isinstance(part, ToolReturnPart) and part.tool_name == "search_text"
            for part in latest_message.parts
        )

        edit_completed = any(
            isinstance(part, ToolReturnPart) and part.tool_name == "edit_note"
            for part in latest_message.parts
        )

        if edit_completed:
            return ModelResponse(parts=[TextPart("Edición terminada.")])

        if not search_completed:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="search_text",
                        args={"terms": ["ollama"]},
                        tool_call_id="search-1",
                    )
                ]
            )

        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="edit_note",
                    args={
                        "path": "ollama.md",
                        "content": "# Ollama\nTexto actualizado.\n",
                    },
                    tool_call_id="edit-1",
                )
            ]
        )

    agent = create_agent(FunctionModel(simulated_model))
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_path))
    monkeypatch.setenv("TRACE_PATH", str(tmp_path / "operations.jsonl"))
    get_settings.cache_clear()

    inputs = iter(["Busca Ollama y propón una actualización.", answer, "salir"])

    def simulated_input(prompt: str) -> str:
        response = next(inputs)
        if response == "s" and external_content is not None:
            note_path.write_bytes(external_content)
        return response

    monkeypatch.setattr("builtins.input", simulated_input)

    try:
        cli.run_chat(agent)
    finally:
        get_settings.cache_clear()

    assert note_path.read_bytes() == expected_content


@pytest.mark.parametrize(
    ("answer", "expected_path", "absent_path"),
    [
        pytest.param("s", "trash/ollama.md.trash", "ollama.md", id="approved"),
        pytest.param("n", "ollama.md", "trash/ollama.md.trash", id="rejected"),
    ],
)
def test_run_chat__delete_reviewed_after_search__respects_decision_and_preserves_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    answer: str,
    expected_path: str,
    absent_path: str,
) -> None:
    """Simula búsqueda y revisión de un borrado por CLI.
    Aceptar mueve la nota a la papelera; rechazar la conserva en su ubicación,
    manteniendo en ambos casos sus bytes originales."""

    original_content = b"# Ollama\nEjecuta modelos localmente.\n"
    (tmp_path / "ollama.md").write_bytes(original_content)

    def simulated_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        latest_message = messages[-1]
        assert isinstance(latest_message, ModelRequest)
        completed_tools = {
            part.tool_name
            for part in latest_message.parts
            if isinstance(part, ToolReturnPart)
        }
        if "delete_note" in completed_tools:
            return ModelResponse(parts=[TextPart("Operación terminada.")])
        if "search_text" in completed_tools:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="delete_note",
                        args={"path": "ollama.md"},
                        tool_call_id="delete-1",
                    )
                ]
            )
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="search_text",
                    args={"terms": ["ollama"]},
                    tool_call_id="search-1",
                )
            ]
        )

    agent = create_agent(FunctionModel(simulated_model))
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_path))
    monkeypatch.setenv("TRACE_PATH", str(tmp_path / "operations.jsonl"))
    get_settings.cache_clear()
    inputs = iter(["Busca la nota de Ollama y bórrala.", answer, "salir"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    try:
        cli.run_chat(agent)
    finally:
        get_settings.cache_clear()
    assert (tmp_path / expected_path).read_bytes() == original_content
    assert not (tmp_path / absent_path).exists()


def test_create_agent__search_requested__returns_matching_note_to_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un modelo simulado solicita una búsqueda real y recibe la nota coincidente.
    Comprueba que solo las notas devueltas quedan registradas como leídas."""
    note_content = "# Ollama\nEjecuta modelos localmente."
    (tmp_path / "ollama.md").write_text(note_content, encoding="utf-8")
    (tmp_path / "gardening.md").write_text(
        "# Jardinería\nCuidados del romero.", encoding="utf-8"
    )
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_path))
    get_settings.cache_clear()

    def simulated_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
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
