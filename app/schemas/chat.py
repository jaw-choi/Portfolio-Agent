from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="사용자 질문")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="LLM 또는 echo 응답")
