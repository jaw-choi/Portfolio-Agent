from unittest.mock import MagicMock, patch

from app.core.prompts import SYSTEM_PROMPT
from app.services import llm_client


def test_get_completion_passes_system_prompt():
    llm_client._client = None
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="ok")]

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.return_value = mock_response

        result = llm_client.get_completion("안녕")

    llm_client._client = None
    assert result == "ok"
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["system"] == SYSTEM_PROMPT
    assert kwargs["messages"] == [{"role": "user", "content": "안녕"}]
