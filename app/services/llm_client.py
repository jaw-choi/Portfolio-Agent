import anthropic

from app.core.prompts import SYSTEM_PROMPT, build_user_message

_client: anthropic.Anthropic | None = None

_REQUEST_TIMEOUT_SECONDS = 30.0
_MAX_RETRIES = 2


class LLMClientError(Exception):
    """LLM 호출이 실패했을 때 발생하는 예외."""


_RESPOND_TOOL = {
    "name": "respond",
    "description": "사용자 질문에 대한 구조화된 답변을 반환합니다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "description": "사용자 질문에 대한 답변"},
            "reason": {"type": "string", "description": "답변의 근거 또는 이유"},
        },
        "required": ["answer", "reason"],
    },
}


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            timeout=_REQUEST_TIMEOUT_SECONDS,
            max_retries=_MAX_RETRIES,
        )
    return _client


def get_completion(message: str, context_chunks: list[dict] | None = None) -> dict:
    user_content = build_user_message(message, context_chunks or [])
    try:
        response = _get_client().messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[_RESPOND_TOOL],
            tool_choice={"type": "tool", "name": "respond"},
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APITimeoutError as exc:
        raise LLMClientError("LLM 응답 시간이 초과되었습니다.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMClientError("LLM 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요.") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMClientError("LLM 서버에 연결할 수 없습니다.") from exc
    except anthropic.APIStatusError as exc:
        raise LLMClientError(f"LLM 호출이 실패했습니다 (status={exc.status_code}).") from exc

    tool_use = next(block for block in response.content if block.type == "tool_use")
    return tool_use.input
