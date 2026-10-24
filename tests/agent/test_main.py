import pytest
from pydantic import SecretStr
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.agent import main as cli
from app.shared.config import DeepSeekSettings


def test_main__two_user_turns__passes_previous_exchange_to_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
