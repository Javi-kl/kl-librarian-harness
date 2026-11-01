import pytest
import logging

from pathlib import Path
from pydantic import SecretStr
from pydantic_ai.messages import (
    ModelRequest,
    ToolCallPart,
    ToolReturnPart,
    ModelMessage,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.agent import main as cli
from app.shared.config import DeepSeekSettings, get_settings


def test_main__two_user_turns__passes_previous_exchange_to_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simula dos entradas por CLI y comprueba que la segunda petición al modelo
    incluye la primera entrada, su respuesta y el nuevo mensaje."""

    requests: list[list[ModelMessage]] = []

    def simulated_model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        requests.append(list(messages))
        return ModelResponse(parts=[TextPart("Respuesta simulada.")])

    settings = DeepSeekSettings.model_construct(
        DEEPSEEK_API_KEY=SecretStr("test-key"), DEEPSEEK_MODEL="test"
    )
    monkeypatch.setattr(cli.DeepSeekSettings, "model_validate", lambda data: settings)
    monkeypatch.setattr(
        cli, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(simulated_model)
    )
    inputs = iter(["Busca notas sobre Ollama.", "Explícame el resultado.", "salir"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    cli.main()

    assert len(requests) == 2
    conversation_parts = [part for message in requests[1] for part in message.parts]
    assert [type(part) for part in conversation_parts] == [
        UserPromptPart,
        TextPart,
        UserPromptPart,
    ]
    assert [
        part.content
        for part in conversation_parts
        if isinstance(part, (UserPromptPart, TextPart))
    ] == [
        "Busca notas sobre Ollama.",
        "Respuesta simulada.",
        "Explícame el resultado.",
    ]


def test_main__edit_approved_after_search__shows_diff_and_writes_proposed_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Simula búsqueda, solicitud de edición y aceptación por CLI, usando las tools
    reales sobre una nota temporal. Comprueba el diff mostrado y el contenido escrito."""

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

    settings = DeepSeekSettings.model_construct(
        DEEPSEEK_API_KEY=SecretStr("test-key"), DEEPSEEK_MODEL="test"
    )
    monkeypatch.setattr(cli.DeepSeekSettings, "model_validate", lambda data: settings)
    monkeypatch.setattr(
        cli, "OpenAIChatModel", lambda *args, **kwargs: FunctionModel(simulated_model)
    )
    monkeypatch.setenv("KB_VAULT_PATH", str(tmp_path))
    get_settings.cache_clear()

    inputs = iter(["Busca Ollama y propón una actualización.", "s", "salir"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    caplog.set_level(logging.INFO, logger=cli.__name__)

    try:
        cli.main()
    finally:
        get_settings.cache_clear()

    assert "-Ejecuta modelos localmente.\n" in caplog.text
    assert "+Texto actualizado.\n" in caplog.text
    assert note_path.read_bytes() == b"# Ollama\nTexto actualizado.\n"
