from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="사용자 질문")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="사용자 질문에 대한 답변")
    reason: str = Field(..., description="답변의 근거 또는 이유")
    sources: list[str] = Field(default_factory=list, description="답변에 사용된 출처 목록")
