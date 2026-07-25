from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="업로드된 문서의 고유 ID")
    filename: str = Field(..., description="업로드된 원본 파일명")
    size_bytes: int = Field(..., description="파일 크기 (바이트)")
    status: str = Field(..., description="업로드 처리 상태")
    text_length: int = Field(..., description="추출된 텍스트 길이 (문자 수)")
    chunk_count: int = Field(..., description="생성된 청크 개수")
