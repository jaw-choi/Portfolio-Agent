SYSTEM_PROMPT = (
    "당신은 사용자의 커리어 지식 에이전트입니다. "
    "Obsidian, 블로그, 포트폴리오, GitHub에 흩어진 사용자의 개발 경험을 바탕으로 질문에 답변합니다. "
    "모르는 내용은 추측하지 말고 모른다고 답하세요. "
    "답변은 한국어로, 간결하고 근거 중심으로 작성하세요."
)


def build_user_message(message: str, context_chunks: list[dict]) -> str:
    if not context_chunks:
        return message

    context_block = "\n\n".join(
        f"[{i}] 출처: {chunk.get('filename') or chunk.get('source_url') or chunk['document_id']}\n"
        f"{chunk['text']}"
        for i, chunk in enumerate(context_chunks, start=1)
    )
    return (
        "다음은 질문과 관련된 참고 자료입니다. 이 자료에 근거해서만 답변하고, "
        "자료에 없는 내용은 모른다고 답하세요.\n\n"
        f"{context_block}\n\n"
        f"질문: {message}"
    )
