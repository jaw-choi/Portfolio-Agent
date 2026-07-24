import time

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.core.chat_log import get_logs, log_chat
from app.ingestion.storage import UnsupportedFileTypeError, save_upload
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentUploadResponse
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
    start = time.perf_counter()
    try:
        result = get_completion(request.message)
        response = ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {exc}") from exc

    response_time_ms = (time.perf_counter() - start) * 1000
    log_chat(request.message, response.answer, response_time_ms)
    return response


@app.get("/logs")
def read_logs(limit: int = 20) -> list[dict]:
    return get_logs(limit)


@app.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    content = await file.read()
    try:
        result = save_upload(file.filename, content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DocumentUploadResponse(**result)