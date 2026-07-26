from pydantic import BaseModel, Field


class GithubCrawlRequest(BaseModel):
    username: str = Field(..., description="크롤링할 GitHub 사용자명")


class GithubCrawlFailure(BaseModel):
    url: str = Field(..., description="README 조회에 실패한 저장소 URL")
    error: str = Field(..., description="실패 사유")


class GithubRepoResult(BaseModel):
    document_id: str = Field(..., description="저장된 문서의 고유 ID")
    url: str = Field(..., description="원본 저장소 URL")
    title: str = Field(..., description="저장소 이름")
    text_length: int = Field(..., description="추출된 텍스트 길이 (문자 수)")
    chunk_count: int = Field(..., description="생성된 청크 개수")


class GithubCrawlResponse(BaseModel):
    username: str = Field(..., description="크롤링한 GitHub 사용자명")
    crawled_count: int = Field(..., description="README를 정상적으로 가져온 저장소 개수")
    repos: list[GithubRepoResult]
    failed: list[GithubCrawlFailure]
