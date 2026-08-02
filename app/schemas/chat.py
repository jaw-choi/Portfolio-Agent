from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="사용자 질문")
    conversation_id: str | None = Field(
        None, description="대화 세션 ID. 없으면 새 대화로 시작하고 새 ID를 발급합니다."
    )


class ChatSource(BaseModel):
    document_id: str = Field(..., description="원본 문서 ID")
    filename: str | None = Field(None, description="출처 문서명")
    source_url: str | None = Field(None, description="출처 URL (있는 경우)")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="사용자 질문에 대한 답변")
    reason: str = Field(..., description="답변의 근거 또는 이유")
    sources: list[ChatSource] = Field(
        default_factory=list, description="답변에 사용된 출처 목록 (검색된 청크 기반)"
    )
    conversation_id: str = Field(..., description="이 대화의 세션 ID. 다음 요청에 그대로 전달하면 대화가 이어집니다.")
