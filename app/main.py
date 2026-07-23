from fastapi import FastAPI, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_client import get_completion

app = FastAPI(
    title="Personal Career Knowledge Agent",
    description=(
        "Obsidian, Blog, Portfolio, GitHub에 분산된 "
        "개발 경험을 통합하고 검색하는 개인 지식 RAG 서비스"
    ),
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "Personal Career Knowledge Agent is running"
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "personal-career-knowledge-agent",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = get_completion(request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {exc}") from exc
    return ChatResponse(reply=reply)