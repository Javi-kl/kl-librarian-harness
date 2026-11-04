from pathlib import Path
import pytest

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    ToolCallPart,
)
from pydantic_ai.usage import UsageLimits
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.test import TestModel

from app.guardrails.state import ConversationState
from app.agent.runtime import create_agent
from app.shared.config import get_settings


def test_create_agent__initial_configuration__exposes_management_tools():
    """Inspecciona las herramientas ofrecidas al modelo y comprueba que el contexto
    interno de búsqueda no aparece entre los argumentos que puede proporcionar."""

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
        "delete_note",
    ]
    tool = parameters.function_tools[0]
    assert set(tool.parameters_json_schema["properties"]) == {"terms"}


@pytest.mark.parametrize(
    ("tool_name", "args"),
    [
        pytest.param(
            "edit_note",
            {"path": "gardening.md", "content": "Contenido nuevo."},
            id="edit",
        ),
        pytest.param(
            "delete_note",
            {"path": "gardening.md"},
            id="delete",
        ),
    ],
)
def test_create_agent__mutation_requested__defers_call_without_changing_note(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tool_name: str,
    args: dict[str, str],
):
    """Simula una solicitud de edición o borrado y comprueba que queda pendiente
    de aprobación, conservando los argumentos y la nota original."""

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
                    tool_name=tool_name,
                    args=args,
                    tool_call_id="mutation-1",
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
    assert pending_call.tool_name == tool_name
    assert pending_call.tool_call_id == "mutation-1"
    assert pending_call.args_as_dict() == args
    assert tmp_note.read_bytes() == content
