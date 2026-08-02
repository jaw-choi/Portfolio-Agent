"""Compare retrieval quality across top_k values (Week 6 D3).

Queries the real production vector store (app.retrieval.search, current
chunk_size=500/overlap=50) at increasing top_k and measures where
eval_dataset.json's expected_source lands, plus the token-cost tradeoff
of stuffing more chunks into the /chat prompt.

Usage: .venv/Scripts/python.exe scripts/eval_top_k.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.search import search

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DATASET_PATH = REPO_ROOT / "eval_dataset.json"
REPORT_PATH = REPO_ROOT / "docs" / "eval_top_k.md"

TOP_KS = [1, 3, 5, 10, 20]
MAX_K = max(TOP_KS)


def load_dataset() -> list[dict]:
    return json.loads(EVAL_DATASET_PATH.read_text(encoding="utf-8"))


def main() -> None:
    dataset = load_dataset()
    hits = {k: 0 for k in TOP_KS}
    total_chars_by_k = {k: 0 for k in TOP_KS}

    for item in dataset:
        results = search(item["question"], top_k=MAX_K)
        filenames = [r["filename"] for r in results]
        for k in TOP_KS:
            if item["expected_source"] in filenames[:k]:
                hits[k] += 1
            total_chars_by_k[k] += sum(len(r["text"]) for r in results[:k])

    total = len(dataset)
    rows = []
    for k in TOP_KS:
        hit_rate = f"{hits[k]}/{total} ({hits[k] / total:.0%})"
        avg_chars = total_chars_by_k[k] / total
        rows.append((k, hit_rate, avg_chars))
        print(f"top_k={k}: hit={hit_rate}, avg context chars/query={avg_chars:.0f}")

    lines = [
        "# top-k 비교 (Week 6 D3)",
        "",
        f"`eval_dataset.json`의 {total}문항으로 실제 운영 벡터 스토어(현재 chunk_size=500/overlap=50, "
        "528 chunks)에 대해 top_k를 바꿔가며 `app.retrieval.search.search()`를 호출했습니다. "
        "hit@k는 top_k개 결과 안에 정답 문서(`expected_source`)가 포함된 비율이고, "
        "평균 컨텍스트 길이는 그 top_k개 chunk를 `/chat` 프롬프트에 넣을 때 들어가는 총 글자 수의 평균입니다.",
        "",
        "| top_k | hit@k | 평균 컨텍스트 길이(자) |",
        "|---|---|---|",
    ]
    for k, hit_rate, avg_chars in rows:
        current = " (현재 운영값)" if k == 5 else ""
        lines.append(f"| {k}{current} | {hit_rate} | {avg_chars:.0f} |")
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
