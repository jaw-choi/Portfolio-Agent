from pydantic import BaseModel, Field


class PortfolioCrawlRequest(BaseModel):
    portfolio_url: str = Field(..., description="크롤링할 포트폴리오 페이지 URL")


class PortfolioSectionResult(BaseModel):
    document_id: str = Field(..., description="저장된 문서의 고유 ID")
    url: str = Field(..., description="원본 섹션 URL (앵커 포함)")
    title: str = Field(..., description="섹션 제목")
    text_length: int = Field(..., description="추출된 텍스트 길이 (문자 수)")
    chunk_count: int = Field(..., description="생성된 청크 개수")


class PortfolioCrawlResponse(BaseModel):
    portfolio_url: str = Field(..., description="크롤링한 포트폴리오 페이지 URL")
    section_count: int = Field(..., description="추출된 섹션 개수")
    sections: list[PortfolioSectionResult]
