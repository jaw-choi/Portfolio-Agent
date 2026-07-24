from unittest.mock import MagicMock, patch

from app.core.prompts import SYSTEM_PROMPT
from app.services import llm_client


def test_get_completion_returns_structured_answer():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because", "sources": ["doc1"]}
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="tool_use", input=expected)]

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.return_value = mock_response

        result = llm_client.get_completion("안녕")

    llm_client._client = None
    assert result == expected
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["system"] == SYSTEM_PROMPT
    assert kwargs["tool_choice"] == {"type": "tool", "name": "respond"}
    assert kwargs["messages"] == [{"role": "user", "content": "안녕"}]
