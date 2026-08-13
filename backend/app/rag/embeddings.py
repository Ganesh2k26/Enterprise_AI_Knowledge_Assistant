"""
Local embeddings via SentenceTransformers (BAAI/bge-small-en-v1.5) -- no
paid embedding API, no network call per request. The model is loaded once
per process (lazy singleton) and inference is offloaded to a thread so it
never blocks the async event loop.
"""
import asyncio
import threading

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging_config import logger

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()

# bge models recommend prefixing queries (but not documents) with an instruction
# for retrieval tasks -- this measurably improves recall for this model family.
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info(f"Loading local embedding model '{settings.EMBEDDING_MODEL}'...")
                _model = SentenceTransformer(settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE)
                logger.info("Embedding model loaded.")
    return _model


def _embed_sync(texts: list[str], is_query: bool) -> list[list[float]]:
    model = _get_model()
    inputs = [f"{_QUERY_INSTRUCTION}{t}" for t in texts] if is_query else texts
    vectors = model.encode(inputs, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed document chunks (no query instruction prefix)."""
    if not texts:
        return []
    return await asyncio.to_thread(_embed_sync, texts, False)


async def embed_query(text: str) -> list[float]:
    """Embed a single search query (with the bge retrieval instruction prefix)."""
    vectors = await asyncio.to_thread(_embed_sync, [text], True)
    return vectors[0]


async def warmup_embedding_model() -> None:
    """Load the embedding model at startup so the first chat is not delayed."""
    await asyncio.to_thread(_get_model)
