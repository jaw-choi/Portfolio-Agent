# Eval Report (Week 6 D5)

Week 6(평가/튜닝)의 D1~D4 결과를 종합한 최종 리포트입니다.

## 요약

| 항목 | 결과 |
|---|---|
| 평가셋 | `eval_dataset.json`, 30문항, 4개 소스(Obsidian 5, 블로그 15, 포트폴리오 3, GitHub 2) |
| 검색 baseline (chunk_size=500/50, top_k=5) | hit@5 47% (14/30) |
| chunk size 튜닝 (D2) | 200~800 범위에서 ±10%p 이내 — 유의미한 차이 아님 |
| top_k 튜닝 (D3) | top_k=5→10 시 hit-rate 47%→57%, top_k=20이면 67%까지 상승. 가장 효과 큰 손잡이 |
| 프롬프트 (D4) | v1→v2로 "유사도 점수가 아니라 자료 내용으로 관련성 판단" 규칙 추가. 실제 답변 품질 효과는 API 키 부재로 미측정 |
| **적용한 변경** | `DEFAULT_TOP_K`를 5 → **10**으로 변경 (`app/retrieval/search.py`, `app/schemas/search.py`) |

## 1. 검색(Retrieval) 튜닝 결론

D2(`docs/eval_chunk_size.md`)와 D3(`docs/eval_top_k.md`)를 나란히 보면:

- **chunk size**는 200/500/800 사이에서 hit-rate가 30~53% 범위로 오르내리지만, 30문항 표본에서 어느 한쪽이 확실히 낫다고 말하기엔 차이가 너무 작다(±10%p 이내, 즉 문항 3개 차이). 게다가 chunk_size를 바꾸려면 이미 ingest된 70개 문서를 전부 재청크·재임베딩해야 해서 위험 대비 이득이 낮다. **현재 값(500/50) 유지.**
- **top_k**는 5→10→20으로 늘릴수록 hit-rate가 47%→57%→67%로 뚜렷하게, 거의 단조증가한다. 같은 임베딩·같은 chunk로 얻을 수 있는 개선 중 top_k가 가장 leverage가 크다.
- top_k를 올리면 `/chat` 프롬프트에 들어가는 컨텍스트 길이도 비례해서 늘어난다(top_k=5: 평균 2274자 → top_k=10: 4546자). Anthropic 호출 비용·지연시간과 직결되는 트레이드오프다.
- top_k=20까지 가면 개선폭(67%)은 크지만 컨텍스트가 top_k=5 대비 4배(9167자)로, 비용 대비 효율이 급격히 나빠진다. **top_k=10을 채택** — hit-rate 개선(+10%p)과 컨텍스트 비용 증가(약 2배)의 균형점으로 판단했다.
- 이 결정에 따라 `app/retrieval/search.py`의 `DEFAULT_TOP_K`와 `app/schemas/search.py`의 `SearchRequest.top_k` 기본값을 5에서 10으로 실제로 변경했다(테스트 67개 전체 통과 확인).

## 2. 프롬프트(Generation) 튜닝 결론

`prompt_log.md`(D4)에 정리했듯, v1→v2 변경은 Week 4 D5에서 발견한 "코사인 유사도 점수가 관련성을 신뢰성 있게 구분하지 못한다"는 문제를 정면으로 겨냥했다 — 검색 단계에서 점수 기반 필터링(MIN_SIMILARITY)을 시도했다가 폐기했던 것과 같은 문제를, v2에서는 프롬프트로 옮겨 "점수가 아니라 자료 내용을 직접 판단하라"고 LLM에 위임했다.

**측정하지 못한 것**: 이 저장소에는 `ANTHROPIC_API_KEY`가 없어(`demo.md` 참고) v1과 v2가 실제 응답의 "근거 없는 답변" 비율을 얼마나 바꾸는지 실측 비교는 못했다. 논리적 근거(위 단락)만 있고 실증 데이터는 없다는 게 이 튜닝 라운드의 가장 큰 한계다.

## 3. 다음에 할 일 (API 키 확보 시)

1. `eval_dataset.json`에 "정답 문서가 없는 질문"(예: 저장소에 없는 기술 스택 질문)을 5~10개 추가해, "모른다고 제대로 답하는지"까지 측정할 수 있게 확장.
2. API 키 설정 후 `/chat`을 30(+a)문항에 대해 실제로 호출해 `answer`/`reason`이 검색된 근거와 일치하는지(hallucination 여부) 채점 — 현재는 검색 단계까지만 검증됨.
3. top_k=10 채택 이후 실제 `/chat` 응답 품질이 top_k=5 대비 나아졌는지 재확인 (지금까지의 비교는 검색 hit-rate 기준이지, 최종 답변 품질 기준이 아니다).

## 4. 참고 문서

- `eval_dataset.json` — 평가셋 원본 (Week 6 D1)
- `docs/eval_chunk_size.md` — chunk size 비교 상세 (Week 6 D2)
- `docs/eval_top_k.md` — top-k 비교 상세 (Week 6 D3)
- `prompt_log.md` — 프롬프트 변경 이력 (Week 6 D4)
- `demo.md` — API 키 부재로 인한 `/chat` 실측 한계 설명 (Week 5 D5)
