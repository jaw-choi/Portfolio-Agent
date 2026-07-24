# Personal Career Knowledge Agent

Obsidian, 블로그, 포트폴리오, GitHub에 분산된 개발 경험과 학습 기록을 하나로 통합해 검색하는 개인 지식 RAG 서비스입니다.

사용자가 질문하면 관련 경험을 찾아 답변과 함께 원본 문서 경로 또는 URL을 함께 제공하는 것을 목표로 합니다.

## 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 환경 변수

`/chat` 엔드포인트는 Anthropic Claude API를 호출합니다. 프로젝트 루트에 `.env` 파일을 만들고 API 키를 설정하세요.

```
ANTHROPIC_API_KEY=your-api-key
```

## 실행

```bash
uvicorn app.main:app --reload
```

서버가 뜨면 `http://127.0.0.1:8000`에서 확인할 수 있습니다.

## API 예시

**서버 상태 확인**

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "healthy", "service": "personal-career-knowledge-agent"}
```

**질문하기**

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"내가 해결한 트러블슈팅 경험을 정리해줘\"}"
```

```json
{"answer": "...", "reason": "...", "sources": []}
```

**최근 대화 로그 조회**

```bash
curl "http://127.0.0.1:8000/logs?limit=5"
```

```json
[{"timestamp": "...", "message": "...", "answer": "...", "response_time_ms": 812.4}]
```

**문서 업로드**

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -F "file=@notes.txt"
```

```json
{"document_id": "...", "filename": "notes.txt", "size_bytes": 123, "status": "uploaded", "text_length": 118}
```

## 테스트

```bash
pytest
```

## 구현 범위 (현재)

- FastAPI 서버, `/health`, `/chat`, `/logs`, `/documents` 엔드포인트
- Pydantic 스키마 기반 요청/응답 검증 (`app/schemas/chat.py`, `app/schemas/document.py`)
- Claude API 연동 (`app/services/llm_client.py`) — system/user 프롬프트 분리(`app/core/prompts.py`), tool-use 기반 구조화 응답(`answer`/`reason`/`sources`), 타임아웃·재시도·에러 처리
- 질문/응답/응답시간 로그 저장 및 조회 (`app/core/chat_log.py`, `/logs`)
- PDF/TXT 파일 업로드 (`app/ingestion/storage.py`) — `data/raw/`에 저장, 지원하지 않는 확장자는 400 반환
- 업로드 시 텍스트 추출/정제 (`app/ingestion/parser.py`) — PDF는 `pypdf`, TXT는 직접 읽어 공백/빈 줄 정리 후 `data/processed/`에 저장
- pytest 테스트 (`tests/test_api.py`, `tests/test_llm_client.py`, `tests/test_chat_log.py`, `tests/test_ingestion_storage.py`, `tests/test_ingestion_parser.py`)

## 다음 작업 (미착수)

- chunk 분할 (`chunker.py`)
- 문서 메타데이터 DB 저장 (문서명/페이지/chunk)
- 공통 Document 형식 변환 및 Vector DB 색인·검색 (`app/retrieval`)
- 답변과 함께 출처(문서 경로 또는 URL) 반환
- 근거 없는 질문에는 "확인할 수 없음"으로 응답
