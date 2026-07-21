from fastapi import FastAPI

from app.schemas.chat import ChatRequest, ChatResponse

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
    # TODO: 2주차에 llm_client.py를 통한 실제 LLM 호출로 교체
    return ChatResponse(reply=f"Echo: {request.message}")