import time

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.core.chat_log import get_logs, log_chat
from app.ingestion.blog_crawler import crawl_blog
from app.ingestion.github_crawler import crawl_github
from app.ingestion.metadata_db import list_documents
from app.ingestion.parser import extract_text
from app.ingestion.pipeline import ingest_text
from app.ingestion.portfolio_crawler import crawl_portfolio
from app.ingestion.storage import UnsupportedFileTypeError, save_upload
from app.retrieval.search import search as search_documents
from app.schemas.blog import BlogCrawlRequest, BlogCrawlResponse, BlogPostResult
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.schemas.document import DocumentUploadResponse
from app.schemas.github import GithubCrawlRequest, GithubCrawlResponse, GithubRepoResult
from app.schemas.portfolio import (
    PortfolioCrawlRequest,
    PortfolioCrawlResponse,
    PortfolioSectionResult,
)
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
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


def _sources_from_chunks(chunks: list[dict]) -> list[ChatSource]:
    seen = set()
    sources = []
    for chunk in chunks:
        key = (chunk.get("filename"), chunk.get("source_url"))
        if key == (None, None) or key in seen:
            continue
        seen.add(key)
        sources.append(ChatSource(filename=key[0], source_url=key[1]))
    return sources


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    try:
        context_chunks = search_documents(request.message)
        result = get_completion(request.message, context_chunks)
        response = ChatResponse(
            answer=result["answer"],
            reason=result["reason"],
            sources=_sources_from_chunks(context_chunks),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"답변 생성 실패: {exc}") from exc

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


@app.post("/github/crawl", response_model=GithubCrawlResponse)
def crawl_github_endpoint(request: GithubCrawlRequest) -> GithubCrawlResponse:
    result = crawl_github(request.username)

    repos = []
    for doc in result["documents"]:
        ingested = ingest_text(
            document_id=doc["document_id"],
            filename=doc["title"],
            text=doc["text"],
            status="crawled",
            size_bytes=len(doc["text"].encode("utf-8")),
            source_url=doc["url"],
        )
        repos.append(
            GithubRepoResult(
                document_id=doc["document_id"],
                url=doc["url"],
                title=doc["title"],
                **ingested,
            )
        )

    return GithubCrawlResponse(
        username=request.username,
        crawled_count=len(repos),
        repos=repos,
        failed=result["failed"],
    )


@app.post("/search", response_model=SearchResponse)
def search_endpoint(request: SearchRequest) -> SearchResponse:
    try:
        results = search_documents(request.query, request.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SearchResponse(
        query=request.query,
        results=[SearchResult(**result) for result in results],
    )