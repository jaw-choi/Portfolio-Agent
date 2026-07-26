from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 질의")
    top_k: int = Field(5, description="반환할 최대 결과 개수", ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: str = Field(..., description="청크 고유 ID")
    document_id: str = Field(..., description="원본 문서 ID")
    chunk_index: int = Field(..., description="문서 내 청크 순번")
    text: str = Field(..., description="청크 텍스트")
    distance: float = Field(..., description="질의와의 벡터 거리 (작을수록 유사)")
    filename: str | None = Field(None, description="원본 문서명")
    source_url: str | None = Field(None, description="원본 문서 URL (있는 경우)")


class SearchResponse(BaseModel):
    query: str = Field(..., description="검색 질의")
    results: list[SearchResult]
