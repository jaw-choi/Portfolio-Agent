"""Compare retrieval quality across chunk sizes (Week 6 D2).

Rebuilds an ephemeral (in-memory) Chroma index at each candidate
chunk_size/overlap from the already-processed text in data/processed/,
so the real production vector store (data/vector_store) is untouched.
Scores each candidate against eval_dataset.json's expected_source.

Usage: .venv/Scripts/python.exe scripts/eval_chunk_size.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb

from app.ingestion.chunker import chunk_text
from app.ingestion.metadata_db import list_documents
from app.ingestion.parser import PROCESSED_DIR
from app.retrieval.embedder import embed_text, embed_texts

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DATASET_PATH = REPO_ROOT / "eval_dataset.json"
REPORT_PATH = REPO_ROOT / "docs" / "eval_chunk_size.md"

# (chunk_size, overlap); 500/50 is the current production default (chunker.py)
CANDIDATES = [(200, 20), (500, 50), (800, 80)]
REPORT_KS = [1, 3, 5]


def load_dataset() -> list[dict]:
    return json.loads(EVAL_DATASET_PATH.read_text(encoding="utf-8"))


def build_index(chunk_size: int, overlap: int) -> tuple[chromadb.Collection, dict[str, str]]:
    docs = list_documents()
    filename_by_doc = {doc["document_id"]: doc["filename"] for doc in docs}

    all_chunks = []
    for document_id in filename_by_doc:
        processed_path = PROCESSED_DIR / f"{document_id}.txt"
        if not processed_path.exists():
            continue
        text = processed_path.read_text(encoding="utf-8")
        all_chunks.extend(chunk_text(document_id, text, chunk_size=chunk_size, overlap=overlap))

    client = chromadb.EphemeralClient()
    collection = client.create_collection(
        f"eval_chunk_{chunk_size}_{overlap}", metadata={"hnsw:space": "cosine"}
    )
    if all_chunks:
        embeddings = embed_texts([chunk["text"] for chunk in all_chunks])
        collection.add(
            ids=[chunk["chunk_id"] for chunk in all_chunks],
            embeddings=embeddings,
            documents=[chunk["text"] for chunk in all_chunks],
            metadatas=[{"document_id": chunk["document_id"]} for chunk in all_chunks],
        )
    return collection, filename_by_doc


def evaluate(
    collection: chromadb.Collection, filename_by_doc: dict[str, str], dataset: list[dict]
) -> dict[str, str]:
    max_k = max(REPORT_KS)
    hits = {k: 0 for k in REPORT_KS}
    for item in dataset:
        query_embedding = embed_text(item["question"])
        result = collection.query(
            query_embeddings=[query_embedding], n_results=max_k, include=["metadatas"]
        )
        retrieved_filenames = [
            filename_by_doc.get(meta["document_id"]) for meta in result["metadatas"][0]
        ]
        for k in REPORT_KS:
            if item["expected_source"] in retrieved_filenames[:k]:
                hits[k] += 1

    total = len(dataset)
    return {f"hit@{k}": f"{hits[k]}/{total} ({hits[k] / total:.0%})" for k in REPORT_KS}


def main() -> None:
    dataset = load_dataset()
    rows = []
    for chunk_size, overlap in CANDIDATES:
        collection, filename_by_doc = build_index(chunk_size, overlap)
        result = evaluate(collection, filename_by_doc, dataset)
        chunk_count = collection.count()
        label = f"{chunk_size}/{overlap}" + (" (현재 운영값)" if (chunk_size, overlap) == (500, 50) else "")
        rows.append((label, chunk_count, result))
        print(label, "-> chunks:", chunk_count, result)

    lines = [
        "# Chunk size 비교 (Week 6 D2)",
        "",
        f"`eval_dataset.json`의 {len(dataset)}문항을 기준으로, chunk_size/overlap 후보별로 "
        "processed 텍스트를 다시 청크·임베딩한 ephemeral 인덱스에서 검색 품질을 비교했습니다. "
        "실제 운영 벡터 스토어(`data/vector_store`)는 변경하지 않습니다.",
        "",
        "| chunk_size/overlap | 총 chunk 수 | hit@1 | hit@3 | hit@5 |",
        "|---|---|---|---|---|",
    ]
    for label, chunk_count, result in rows:
        lines.append(
            f"| {label} | {chunk_count} | {result['hit@1']} | {result['hit@3']} | {result['hit@5']} |"
        )
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
