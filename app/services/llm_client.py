import anthropic

from app.core.prompts import SYSTEM_PROMPT

_client: anthropic.Anthropic | None = None

_RESPOND_TOOL = {
    "name": "respond",
    "description": "사용자 질문에 대한 구조화된 답변을 반환합니다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "description": "사용자 질문에 대한 답변"},
            "reason": {"type": "string", "description": "답변의 근거 또는 이유"},
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "답변에 사용된 출처 목록. 없으면 빈 배열.",
            },
        },
        "required": ["answer", "reason", "sources"],
    },
}


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def get_completion(message: str) -> dict:
    response = _get_client().messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[_RESPOND_TOOL],
        tool_choice={"type": "tool", "name": "respond"},
        messages=[{"role": "user", "content": message}],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    return tool_use.input
