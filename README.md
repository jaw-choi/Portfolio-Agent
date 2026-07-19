# OfficeDoc AI Agent

사내 문서를 업로드하고 문서 내용을 기반으로 질문에 답변하는 RAG 서비스입니다.

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload