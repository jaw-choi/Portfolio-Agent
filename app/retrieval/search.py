from app.ingestion.metadata_db import get_document_metadata
from app.retrieval.embedder import embed_text
from app.retrieval.vector_store import query as query_vector_store

DEFAULT_TOP_K = 5


def search(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    query_embedding = embed_text(query)
    raw = query_vector_store(query_embedding, top_k)

    ids = raw["ids"][0]
    documents = raw["documents"][0]
    metadatas = raw["metadatas"][0]
    distances = raw["distances"][0]

    results = []
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        document_id = metadata["document_id"]
        document_meta = get_document_metadata(document_id) or {}

        results.append(
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "chunk_index": metadata["chunk_index"],
                "text": text,
                "similarity": 1 - distance,
                "filename": document_meta.get("filename"),
                "source_url": document_meta.get("source_url"),
            }
        )
    return results
