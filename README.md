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

## 테스트

```bash
pytest
```

## 구현 범위 (현재)

- FastAPI 서버, `/health`, `/chat` 엔드포인트
- Pydantic 스키마 기반 요청/응답 검증 (`app/schemas/chat.py`)
- Claude API 연동 (`app/services/llm_client.py`) — `/chat`이 실제 LLM 응답을 반환
- pytest API 테스트 (`tests/test_api.py`)

## 다음 작업 (미착수)

- Obsidian / GitHub README / 포트폴리오 PDF / 블로그 문서 읽기 (`app/ingestion`)
- 공통 Document 형식 변환 및 Vector DB 색인·검색 (`app/retrieval`)
- 답변과 함께 출처(문서 경로 또는 URL) 반환
- 근거 없는 질문에는 "확인할 수 없음"으로 응답
