from pathlib import Path

import chromadb

from app.retrieval.embedder import embed_texts

VECTOR_STORE_DIR = Path("data/vector_store")
COLLECTION_NAME = "chunks"


def _get_collection():
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    return client.get_or_create_collection(COLLECTION_NAME)


def add_chunks(chunks: list[dict]) -> None:
    if not chunks:
        return

    collection = _get_collection()
    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    collection.upsert(
        ids=[chunk["chunk_id"] for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {"document_id": chunk["document_id"], "chunk_index": chunk["chunk_index"]}
            for chunk in chunks
        ],
    )
