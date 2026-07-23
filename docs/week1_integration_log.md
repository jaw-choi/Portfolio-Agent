# 1주차 통합 실행 기록 (2026-07-24)

주중(7/22~7/23) 결과물을 직접 실행해 하나의 흐름으로 동작하는지 확인한 기록.

## 실행한 것

1. `uvicorn app.main:app` 로 서버 직접 기동
2. `curl`로 `/`, `/health`, `/chat` 직접 호출
3. `pytest` 전체 테스트 실행

## 결과

| 확인 항목 | 결과 |
|---|---|
| `GET /` | 200, `{"message": "Personal Career Knowledge Agent is running"}` |
| `GET /health` | 200, `{"status": "healthy", "service": "personal-career-knowledge-agent"}` |
| `POST /chat` (빈 message) | 422, Pydantic 검증 오류 정상 반환 |
| `POST /chat` (정상 message) | **최초 실행 시 500, 본문 없이 "Internal Server Error"만 반환 (오류 발견)** |
| `pytest` (3개) | 3 passed |

## 발견한 오류와 수정

**문제:** `ANTHROPIC_API_KEY`가 설정되지 않은 상태에서 `/chat`을 호출하면 `anthropic` SDK가
`TypeError("Could not resolve authentication method...")`를 던지는데, `app/main.py`의
`chat()`이 이를 잡지 않아 FastAPI가 내용 없는 500 응답만 반환했음 (`test_api.py`의
서버 오류 테스트는 mock으로만 검증해서 이 문제를 못 잡았음 — 직접 실행 테스트에서 발견).

**수정:** `app/main.py`의 `chat()`에서 `get_completion()` 호출을 `try/except`로 감싸고,
실패 시 `HTTPException(500, detail="LLM 호출 실패: {원인}")`으로 명확한 에러 메시지를 반환하도록 변경.

**수정 후 재확인:**

```
POST /chat {"message": "hello"}
-> 500
{"detail": "LLM 호출 실패: \"Could not resolve authentication method. Expected one of api_key, auth_token, or credentials to be set. Or for one of the `X-Api-Key` or `Authorization` headers to be explicitly omitted\""}
```

내용이 있는 에러 메시지로 개선됨. (`ANTHROPIC_API_KEY`를 설정하면 정상 응답으로 전환될 것으로 예상 — 실제 키로는 아직 미검증)

## 미완료/알려진 제약

- 실제 Claude API 키(`ANTHROPIC_API_KEY`)가 이 환경에 설정되어 있지 않아, `/chat`의 **정상 LLM 응답 경로는 실제 키로 검증되지 않음** — mock을 통한 테스트만 통과한 상태.
- `app/ingestion`, `app/retrieval`, `app/core` 는 아직 빈 스텁 (`__init__.py`만 존재) — RAG 파이프라인 미착수.

## 최종 확인

- `pytest -v` : 3 passed
- 서버 직접 기동 후 `/`, `/health`, `/chat`(입력 오류·정상 입력) 모두 예상대로 동작 확인
