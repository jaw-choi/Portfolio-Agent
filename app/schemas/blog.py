from pydantic import BaseModel, Field


class BlogCrawlRequest(BaseModel):
    blog_url: str = Field(..., description="크롤링할 블로그 루트 URL")


class BlogCrawlFailure(BaseModel):
    url: str = Field(..., description="크롤링에 실패한 글 URL")
    error: str = Field(..., description="실패 사유")


class BlogPostResult(BaseModel):
    document_id: str = Field(..., description="저장된 문서의 고유 ID")
    url: str = Field(..., description="원본 글 URL")
    title: str = Field(..., description="글 제목")
    text_length: int = Field(..., description="추출된 텍스트 길이 (문자 수)")
    chunk_count: int = Field(..., description="생성된 청크 개수")


class BlogCrawlResponse(BaseModel):
    blog_url: str = Field(..., description="크롤링한 블로그 루트 URL")
    crawled_count: int = Field(..., description="정상적으로 크롤링된 글 개수")
    posts: list[BlogPostResult]
    failed: list[BlogCrawlFailure]
