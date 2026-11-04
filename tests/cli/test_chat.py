import logging
from unittest.mock import Mock

import pytest
from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.cli.chat import run_chat


def test_run_chat__two_user_turns__forwards_history_and_displays_responses(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sustituye el agente y comprueba que el CLI le pasa la nueva entrada y el
    historial anterior, y muestra sus respuestas sin ejecutar tools ni modelos."""
    previous_exchange = [
        ModelRequest(parts=[UserPromptPart("Busca notas sobre Ollama.")]),
        ModelResponse(parts=[TextPart("Primera respuesta.")]),
    ]
    first_result = Mock(output="Primera respuesta.")
    first_result.all_messages.return_value = previous_exchange
    first_result.new_messages.return_value = []
    second_result = Mock(output="Segunda respuesta.")
    second_result.all_messages.return_value = previous_exchange
    second_result.new_messages.return_value = []
    agent = Mock(spec=Agent)
    agent.run_sync.side_effect = [first_result, second_result]
    inputs = iter(["Busca notas sobre Ollama.", "Explícame el resultado.", "salir"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    caplog.set_level(logging.INFO, logger="app.cli.chat")

    run_chat(agent)

    assert agent.run_sync.call_count == 2
    first_call, second_call = agent.run_sync.call_args_list
    assert first_call.args == ("Busca notas sobre Ollama.",)
    assert second_call.args == ("Explícame el resultado.",)
    assert second_call.kwargs["message_history"] == previous_exchange
    assert "Primera respuesta." in caplog.text
    assert "Segunda respuesta." in caplog.text
