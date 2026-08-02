from unittest.mock import MagicMock, patch

import anthropic
import httpx
import pytest

from app.core.prompts import SYSTEM_PROMPT
from app.services import llm_client


def _dummy_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _dummy_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, request=_dummy_request())


def test_get_completion_returns_structured_answer():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because"}
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
    sent_content = kwargs["messages"][0]["content"]
    assert sent_content.endswith("질문: 안녕")


def test_get_completion_includes_context_chunks_in_prompt():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because"}
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="tool_use", input=expected)]

    context_chunks = [
        {
            "document_id": "doc1",
            "text": "싱글톤 설명 내용",
            "filename": "cs_singleton.md",
            "source_url": None,
        }
    ]

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.return_value = mock_response

        result = llm_client.get_completion("싱글톤이 뭐야?", context_chunks)

    llm_client._client = None
    assert result == expected
    _, kwargs = mock_client.messages.create.call_args
    sent_content = kwargs["messages"][0]["content"]
    assert "싱글톤 설명 내용" in sent_content
    assert "cs_singleton.md" in sent_content
    assert sent_content.endswith("질문: 싱글톤이 뭐야?")


def test_get_client_configures_timeout_and_retries():
    llm_client._client = None

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        llm_client._get_client()

    llm_client._client = None
    _, kwargs = mock_anthropic_cls.call_args
    assert kwargs["timeout"] == llm_client._REQUEST_TIMEOUT_SECONDS
    assert kwargs["max_retries"] == llm_client._MAX_RETRIES


@pytest.mark.parametrize(
    ("side_effect", "expected_message"),
    [
        (anthropic.APITimeoutError(request=_dummy_request()), "시간이 초과"),
        (anthropic.APIConnectionError(request=_dummy_request()), "연결할 수 없습니다"),
        (
            anthropic.RateLimitError(
                "rate limited", response=_dummy_response(429), body=None
            ),
            "호출 한도",
        ),
        (
            anthropic.APIStatusError(
                "server error", response=_dummy_response(503), body=None
            ),
            "status=503",
        ),
    ],
)
def test_get_completion_wraps_sdk_errors(side_effect, expected_message):
    llm_client._client = None

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.side_effect = side_effect

        with pytest.raises(llm_client.LLMClientError, match=expected_message):
            llm_client.get_completion("안녕")

    llm_client._client = None
