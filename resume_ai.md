# 이력서 문항 — Personal Career Knowledge Agent (Week 8 D3)

이 프로젝트 하나에 대한 이력서용 문항 초안입니다. 학력·경력 등 다른 항목은 포함하지 않았습니다 — 기존 이력서의 "프로젝트" 섹션에 그대로 붙여 쓰거나, 필요한 문항만 골라 쓰면 됩니다. 모두 이 저장소에서 실제로 구현·검증한 내용에 근거합니다.

## 한 줄 소개

**Personal Career Knowledge Agent** — Obsidian, 블로그, 포트폴리오, GitHub 4개 소스에 흩어진 개발 경험을 통합 검색하는 개인 지식 RAG(FastAPI + ChromaDB + Claude API) 서비스를 설계부터 배포 구성까지 단독 개발.

## 핵심 성과 (이력서용 불릿)

- **RAG 파이프라인을 처음부터 설계·구현**: FastAPI 기반 API 서버에 로컬 한국어 임베딩 모델(`ko-sroberta-multitask`)과 ChromaDB(cosine 유사도) 벡터 검색, Claude API(tool-use 기반 구조화 출력)를 연결해 질문 → 검색 → 근거 기반 답변 파이프라인을 구축.
- **4개 이종 데이터 소스를 하나의 파이프라인으로 통합**: 파일 업로드(Obsidian), 사이트맵 기반 블로그 전체 크롤링(Tistory, 34개 글), HTML 섹션 단위 포트폴리오 크롤링(GitHub Pages, 8개 섹션), GitHub API 기반 README 수집(23개 저장소)을 공통 ingestion 파이프라인으로 통합 — 총 70개 문서·528개 청크.
- **정량적 평가 체계를 구축해 검색 파라미터를 데이터 기반으로 튜닝**: 30문항 평가셋을 직접 설계하고 chunk size·top_k 비교 스크립트를 작성, 검색 hit-rate를 top_k=5(47%)에서 top_k=10(57%)으로 개선하는 근거를 확보하고 실제 운영값에 반영.
- **임베딩 유사도 점수의 신뢰성 한계를 발견하고 설계로 해결**: 코사인 유사도 임계값(threshold) 필터링을 시도했다가, 무관한 질의가 실제 정답보다 더 높은 점수를 받는 사례를 발견해 코드 레벨 필터를 폐기 — 대신 "점수가 아니라 자료 내용으로 관련성을 판단하라"는 프롬프트 규칙으로 문제를 재설계해 해결.
- **RAG 서비스를 컨테이너화하고 DB 계층을 이식 가능하게 리팩터링**: Dockerfile/docker-compose로 앱+PostgreSQL을 구성했고, SQLite 전용으로 짜여 있던 메타데이터 저장소를 `DATABASE_URL` 환경변수 기반으로 전환 — 이 과정에서 SQLite 전용 `rowid` 정렬에 의존하던 실제 이식성 버그를 발견해 함께 수정.
- **테스트로 뒷받침되는 개발**: pytest 기반 단위/통합 테스트 68개를 전 기능(ingestion, 임베딩/검색, LLM 클라이언트, 대화 히스토리, API)에 대해 작성·유지, 기능 추가마다 회귀 없음을 확인하며 반복 개발.
- **실사용 데이터로 라이브 검증하는 습관**: mock이 아닌 실제 수집 데이터(70문서/528청크)로 매 기능을 라이브 호출 검증 — 예를 들어 `.env` 로딩 로직의 숨은 버그(의존성은 있었지만 실제로 호출되지 않던 `load_dotenv()`)를 라이브 테스트 중 발견해 수정.

## 사용 기술

Python, FastAPI, Pydantic, SQLAlchemy(SQLite/PostgreSQL), ChromaDB, sentence-transformers, Anthropic Claude API, Docker/docker-compose, pytest, BeautifulSoup(크롤링), Git

## 참고

- 상세 설계·의사결정 근거는 [`interview_qa.md`](interview_qa.md), [`prompt_log.md`](prompt_log.md), [`eval_report.md`](eval_report.md) 참고.
- 실제 실행 예시는 [`demo.md`](demo.md) 참고.
