import anthropic

from app.core.prompts import SYSTEM_PROMPT, build_user_message, format_context
from app.ingestion.metadata_db import list_documents
from app.retrieval.search import search as search_documents

_client: anthropic.Anthropic | None = None

_REQUEST_TIMEOUT_SECONDS = 30.0
_MAX_RETRIES = 2
DEFAULT_MAX_TURNS = 5


class LLMClientError(Exception):
    """LLM 호출이 실패했을 때 발생하는 예외."""


_RESPOND_TOOL = {
    "name": "respond",
    "description": "사용자 질문에 대한 최종 답변을 구조화해서 제출합니다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "description": "사용자 질문에 대한 답변"},
            "reason": {"type": "string", "description": "답변의 근거 또는 이유"},
        },
        "required": ["answer", "reason"],
    },
}

_SEARCH_TOOL = {
    "name": "search_documents",
    "description": (
        "사용자의 노트, 블로그, 포트폴리오, GitHub README에서 관련 내용을 검색합니다. "
        "주어진 참고 자료로 답하기 부족할 때 다른 검색어나 더 구체적인 검색어로 다시 찾을 때 사용합니다."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "검색어"}},
        "required": ["query"],
    },
}

_LIST_DOCUMENTS_TOOL = {
    "name": "list_documents",
    "description": "수집된 전체 문서 목록(문서명, URL, 청크 수)을 조회합니다. 어떤 자료가 있는지 파악할 때 사용합니다.",
    "input_schema": {"type": "object", "properties": {}},
}

_TOOLS = [_SEARCH_TOOL, _LIST_DOCUMENTS_TOOL, _RESPOND_TOOL]
_FORCE_RESPOND = {"type": "tool", "name": "respond"}


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            timeout=_REQUEST_TIMEOUT_SECONDS,
            max_retries=_MAX_RETRIES,
        )
    return _client


def _create_message(messages: list[dict], tool_choice: dict):
    try:
        return _get_client().messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=_TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )
    except anthropic.APITimeoutError as exc:
        raise LLMClientError("LLM 응답 시간이 초과되었습니다.") from exc
    except anthropic.RateLimitError as exc:
        raise LLMClientError("LLM 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요.") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMClientError("LLM 서버에 연결할 수 없습니다.") from exc
    except anthropic.APIStatusError as exc:
        raise LLMClientError(f"LLM 호출이 실패했습니다 (status={exc.status_code}).") from exc


def _run_tool(name: str, tool_input: dict, collected: list[dict]) -> str:
    if name == "search_documents":
        chunks = search_documents(tool_input["query"])
        if not chunks:
            return "검색 결과가 없습니다. 다른 검색어로 시도하세요."
        start = len(collected) + 1
        collected.extend(chunks)
        return format_context(chunks, start)
    if name == "list_documents":
        documents = list_documents()
        if not documents:
            return "수집된 문서가 없습니다."
        return "\n".join(
            f"- {doc['filename']} ({doc['source_url'] or '업로드 문서'}, chunk {doc['chunk_count']}개)"
            for doc in documents
        )
    raise ValueError(f"알 수 없는 도구입니다: {name}")


def _tool_result(block, collected: list[dict]) -> dict:
    # 도구가 실패해도 루프를 죽이지 않고, 에러 내용을 모델에게 되먹여 스스로 복구하게 한다.
    try:
        content = _run_tool(block.name, block.input, collected)
    except Exception as exc:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"에러: {exc}. 입력을 확인하고 다시 시도하세요.",
            "is_error": True,
        }
    return {"type": "tool_result", "tool_use_id": block.id, "content": content}


def get_completion(
    message: str,
    context_chunks: list[dict] | None = None,
    history: list[dict] | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> dict:
    context_chunks = context_chunks or []
    user_content = build_user_message(message, context_chunks)
    messages = [*(history or []), {"role": "user", "content": user_content}]
    # 참고 자료 번호([1], [2]...)가 추가 검색 결과까지 이어지도록 한 리스트에 모은다.
    collected = list(context_chunks)

    def _result(respond_input: dict) -> dict:
        return {**respond_input, "searched_chunks": collected[len(context_chunks):]}

    for _ in range(max_turns - 1):
        response = _create_message(messages, {"type": "any"})
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        respond = next((block for block in tool_uses if block.name == "respond"), None)
        if respond is not None:
            return _result(respond.input)

        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {"role": "user", "content": [_tool_result(block, collected) for block in tool_uses]}
        )

    # 반복 한도에 도달하면 지금까지 모은 자료로 답하도록 respond를 강제한다.
    response = _create_message(messages, _FORCE_RESPOND)
    respond = next(block for block in response.content if block.type == "tool_use")
    return _result(respond.input)
