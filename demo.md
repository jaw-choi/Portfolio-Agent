# Demo: Personal Career Knowledge Agent

이 문서는 실제로 서버를 띄우고 API를 호출해 얻은 결과로 RAG 파이프라인 전체 흐름(수집 → 검색 → 답변)을 보여줍니다.

## 0. 준비

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

`/chat`이 실제 답변을 생성하려면 `.env`에 `ANTHROPIC_API_KEY`가 필요합니다. 이 저장소는 아직 키가 설정되어 있지 않아 아래 `/chat` 데모는 검색까지의 동작과, 키 미설정 시의 에러 처리를 보여줍니다 (자세한 내용은 [4. 한계](#4-현재-한계) 참고).

## 1. 데이터 현황 (`GET /documents`)

지금까지 4개 소스(Obsidian 샘플 업로드, Tistory 블로그 크롤링, GitHub Pages 포트폴리오 크롤링, GitHub README 크롤링)에서 실제로 수집한 데이터가 쌓여 있습니다.

```
$ curl http://127.0.0.1:8000/documents
```

| 항목 | 값 |
|---|---|
| 문서 수 | 70 (업로드 5 + 블로그 34 + 포트폴리오 8 + GitHub README 23) |
| 총 chunk 수 | 528 |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` (로컬, 한국어 튜닝) |
| 벡터 스토어 | ChromaDB (`cosine` 거리) |

## 2. 검색 (`POST /search`)

실제 벡터 스토어(528 chunks)에 대해 "싱글톤 패턴이 뭐야?"로 질의한 결과입니다. `similarity`는 1에 가까울수록 유사합니다.

```
$ curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "싱글톤 패턴이 뭐야?", "top_k": 3}'
```

```json
{
  "query": "싱글톤 패턴이 뭐야?",
  "results": [
    {
      "chunk_id": "0b251ab253f04162800ce119e7f30cbb_0",
      "document_id": "0b251ab253f04162800ce119e7f30cbb",
      "chunk_index": 0,
      "text": "- 싱글톤과 friend 함께 사용 ## CS - 싱글톤 패턴 ## 1. 한 줄 요약 싱글톤 패턴은 클래스의 인스턴스를 오직 하나만 생성되도록 제한하고, 어디서든 그 인스턴스에 접근할 수 있도록 하는 디자인 패턴이다. ## 2. 왜 필요한가? (Why) - **유일성 보장**: 시스템 내에서 특정 클래스의 인스턴스가 오직 하나만 존재해야 할 때 유용하다. ...",
      "similarity": 0.5922,
      "filename": "cs_singleton.md",
      "source_url": null
    },
    {
      "chunk_id": "0b251ab253f04162800ce119e7f30cbb_3",
      "document_id": "0b251ab253f04162800ce119e7f30cbb",
      "chunk_index": 3,
      "text": "장단점 / 트레이드오프 - **장점**: - 유일한 인스턴스 보장 - 전역적인 접근 제공 - 필요할 때만 인스턴스 생성 - **단점**: - 과도하게 사용하면 전역 변수와 유사한 문제 발생 ...",
      "similarity": 0.4405,
      "filename": "cs_singleton.md",
      "source_url": null
    },
    {
      "chunk_id": "0b251ab253f04162800ce119e7f30cbb_4",
      "document_id": "0b251ab253f04162800ce119e7f30cbb",
      "chunk_index": 4,
      "text": "방법은? - **A**: 멀티스레드 환경에서는 여러 스레드가 동시에 `getInstance()` 메서드를 호출하여 인스턴스를 여러 번 생성할 수 있다. ...",
      "similarity": 0.4252,
      "filename": "cs_singleton.md",
      "source_url": null
    }
  ]
}
```

3개 결과 모두 `cs_singleton.md`의 서로 다른 chunk이고, 가장 관련 있는 "한 줄 요약" 부분이 최상위 유사도(0.59)로 정확히 올라온 것을 확인할 수 있습니다.

## 3. 답변 생성 (`POST /chat`)

`/chat`은 위 검색을 내부적으로 수행한 뒤 그 결과를 LLM 프롬프트에 근거 자료로 넣고, 구조화된 답변(`answer`/`reason`/`sources`)과 대화를 이어갈 `conversation_id`를 반환합니다.

```
$ curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "싱글톤 패턴이 뭐야?"}'
```

**API 키가 설정되어 있을 때 예상되는 응답 형태** (스키마 기준, `app/schemas/chat.py`):

```json
{
  "answer": "...(검색된 자료에 근거한 답변)...",
  "reason": "...([1] cs_singleton.md 참고 등 근거 설명)...",
  "sources": [
    {"filename": "cs_singleton.md", "source_url": null}
  ],
  "conversation_id": "3f9b1c2e-..."
}
```

이어지는 질문에 같은 `conversation_id`를 실어 보내면, 이전 turn들이 대화 맥락으로 함께 전달됩니다 (`app/core/conversation.py`, Week 5 D4).

## 4. 현재 한계

- **`ANTHROPIC_API_KEY` 미설정**: 이 저장소에는 아직 `.env`가 없어 `/chat`의 실제 LLM 호출 단계는 검증하지 못했습니다. 검색(retrieval) 단계까지는 실제 데이터로 정상 동작을 확인했고, 이 상태에서 `/chat`을 호출하면 검색은 성공하고 LLM 호출에서만 아래처럼 인증 오류로 실패합니다 (실제로 재현한 응답):

  ```json
  {
    "detail": "답변 생성 실패: \"Could not resolve authentication method. Expected one of api_key, auth_token, or credentials to be set. Or for one of the `X-Api-Key` or `Authorization` headers to be explicitly omitted\""
  }
  ```

  즉 이 에러는 검색 파이프라인이 아니라 순수하게 LLM 호출 단계에서 발생하며, 이는 "검색이 정상 동작한다"는 방증이기도 합니다.
- 키를 설정하면 3절의 실제 예시가 그대로 재현 가능합니다: `.env`에 `ANTHROPIC_API_KEY=...` 추가 후 서버 재시작.
