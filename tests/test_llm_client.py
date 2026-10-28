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


def _tool_use(name: str, tool_input: dict, block_id: str = "tool_1") -> MagicMock:
    # MagicMock(name=...)은 mock 자체의 이름으로 쓰이므로 name 속성은 따로 지정한다.
    block = MagicMock(type="tool_use", input=tool_input, id=block_id)
    block.name = name
    return block


def _response(*blocks) -> MagicMock:
    response = MagicMock()
    response.content = list(blocks)
    return response


def test_get_completion_returns_structured_answer():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because"}

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.return_value = _response(_tool_use("respond", expected))

        result = llm_client.get_completion("안녕")

    llm_client._client = None
    assert result == {**expected, "searched_chunks": []}
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["system"] == SYSTEM_PROMPT
    assert kwargs["tool_choice"] == {"type": "any"}
    assert {tool["name"] for tool in kwargs["tools"]} == {
        "respond",
        "search_documents",
        "list_documents",
    }
    sent_content = kwargs["messages"][0]["content"]
    assert sent_content.endswith("질문: 안녕")


def test_get_completion_includes_context_chunks_in_prompt():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because"}

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
        mock_client.messages.create.return_value = _response(_tool_use("respond", expected))

        result = llm_client.get_completion("싱글톤이 뭐야?", context_chunks)

    llm_client._client = None
    assert result == {**expected, "searched_chunks": []}
    _, kwargs = mock_client.messages.create.call_args
    sent_content = kwargs["messages"][0]["content"]
    assert "싱글톤 설명 내용" in sent_content
    assert "cs_singleton.md" in sent_content
    assert sent_content.endswith("질문: 싱글톤이 뭐야?")


def test_get_completion_prepends_conversation_history():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because"}

    history = [
        {"role": "user", "content": "첫 질문"},
        {"role": "assistant", "content": "첫 답변"},
    ]

    with patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.return_value = _response(_tool_use("respond", expected))

        result = llm_client.get_completion("두번째 질문", history=history)

    llm_client._client = None
    assert result == {**expected, "searched_chunks": []}
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["messages"][0] == history[0]
    assert kwargs["messages"][1] == history[1]
    assert kwargs["messages"][2]["content"].endswith("질문: 두번째 질문")


def test_agent_loop_runs_search_tool_and_feeds_result_back():
    llm_client._client = None
    context_chunks = [
        {"document_id": "doc0", "text": "처음 검색 결과", "filename": "a.md", "source_url": None}
    ]
    searched = [
        {"document_id": "doc1", "text": "추가 검색 결과", "filename": "b.md", "source_url": None}
    ]
    expected = {"answer": "ok", "reason": "[2] 참고"}

    with (
        patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls,
        patch("app.services.llm_client.search_documents", return_value=searched) as mock_search,
    ):
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.side_effect = [
            _response(_tool_use("search_documents", {"query": "언리얼 트러블슈팅"}, "t1")),
            _response(_tool_use("respond", expected, "t2")),
        ]

        result = llm_client.get_completion("질문", context_chunks)

    llm_client._client = None
    mock_search.assert_called_once_with("언리얼 트러블슈팅")
    assert result == {**expected, "searched_chunks": searched}
    _, kwargs = mock_client.messages.create.call_args
    tool_result = kwargs["messages"][-1]["content"][0]
    assert tool_result["tool_use_id"] == "t1"
    # 처음 받은 자료가 [1]이므로 추가 검색 결과는 [2]부터 이어진다.
    assert tool_result["content"].startswith("[2] 출처: b.md")
    assert "is_error" not in tool_result


def test_agent_loop_feeds_tool_error_back_instead_of_crashing():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "근거 자료 없음"}

    with (
        patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls,
        patch(
            "app.services.llm_client.search_documents",
            side_effect=ValueError("검색어가 비어 있습니다."),
        ),
    ):
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.side_effect = [
            _response(_tool_use("search_documents", {"query": " "}, "t1")),
            _response(_tool_use("respond", expected, "t2")),
        ]

        result = llm_client.get_completion("질문")

    llm_client._client = None
    assert result == {**expected, "searched_chunks": []}
    _, kwargs = mock_client.messages.create.call_args
    tool_result = kwargs["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "검색어가 비어 있습니다." in tool_result["content"]


def test_agent_loop_forces_respond_when_max_turns_reached():
    llm_client._client = None
    expected = {"answer": "ok", "reason": "because"}

    with (
        patch("app.services.llm_client.anthropic.Anthropic") as mock_anthropic_cls,
        patch("app.services.llm_client.search_documents", return_value=[]),
    ):
        mock_client = mock_anthropic_cls.return_value
        mock_client.messages.create.side_effect = [
            _response(_tool_use("search_documents", {"query": "a"}, "t1")),
            _response(_tool_use("respond", expected, "t2")),
        ]

        result = llm_client.get_completion("질문", max_turns=2)

    llm_client._client = None
    assert result == {**expected, "searched_chunks": []}
    calls = mock_client.messages.create.call_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["tool_choice"] == {"type": "any"}
    assert calls[1].kwargs["tool_choice"] == {"type": "tool", "name": "respond"}


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
