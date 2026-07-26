from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "jhgan/ko-sroberta-multitask"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()
