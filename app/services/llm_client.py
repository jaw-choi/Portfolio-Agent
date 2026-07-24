import anthropic

from app.core.prompts import SYSTEM_PROMPT

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def get_completion(message: str) -> str:
    response = _get_client().messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
    )
    return next(block.text for block in response.content if block.type == "text")
