import time

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.core.chat_log import get_logs, log_chat
from app.ingestion.blog_crawler import crawl_blog
from app.ingestion.metadata_db import list_documents
from app.ingestion.parser import extract_text
from app.ingestion.pipeline import ingest_text
from app.ingestion.portfolio_crawler import crawl_portfolio
from app.ingestion.storage import UnsupportedFileTypeError, save_upload
from app.schemas.blog import BlogCrawlRequest, BlogCrawlResponse, BlogPostResult
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentUploadResponse
from app.schemas.portfolio import (
    PortfolioCrawlRequest,
    PortfolioCrawlResponse,
    PortfolioSectionResult,
)
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

    text = extract_text(result["path"])
    ingested = ingest_text(
        document_id=result["document_id"],
        filename=result["filename"],
        text=text,
        status=result["status"],
        size_bytes=result["size_bytes"],
    )

    return DocumentUploadResponse(**result, **ingested)


@app.get("/documents")
def read_documents() -> list[dict]:
    return list_documents()


@app.post("/blog/crawl", response_model=BlogCrawlResponse)
def crawl_blog_endpoint(request: BlogCrawlRequest) -> BlogCrawlResponse:
    result = crawl_blog(request.blog_url)

    posts = []
    for post in result["posts"]:
        ingested = ingest_text(
            document_id=post["document_id"],
            filename=post["title"],
            text=post["text"],
            status="crawled",
            size_bytes=len(post["text"].encode("utf-8")),
            source_url=post["url"],
        )
        posts.append(
            BlogPostResult(
                document_id=post["document_id"],
                url=post["url"],
                title=post["title"],
                **ingested,
            )
        )

    return BlogCrawlResponse(
        blog_url=request.blog_url,
        crawled_count=len(posts),
        posts=posts,
        failed=result["failed"],
    )


@app.post("/portfolio/crawl", response_model=PortfolioCrawlResponse)
def crawl_portfolio_endpoint(request: PortfolioCrawlRequest) -> PortfolioCrawlResponse:
    crawled_sections = crawl_portfolio(request.portfolio_url)

    sections = []
    for section in crawled_sections:
        ingested = ingest_text(
            document_id=section["document_id"],
            filename=section["title"],
            text=section["text"],
            status="crawled",
            size_bytes=len(section["text"].encode("utf-8")),
            source_url=section["url"],
        )
        sections.append(
            PortfolioSectionResult(
                document_id=section["document_id"],
                url=section["url"],
                title=section["title"],
                **ingested,
            )
        )

    return PortfolioCrawlResponse(
        portfolio_url=request.portfolio_url,
        section_count=len(sections),
        sections=sections,
    )