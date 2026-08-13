"""
Hybrid retrieval: semantic search via Chroma (cosine similarity on the local
bge-small embeddings) blended with a lexical term-overlap score, then
deduplicated and compressed to fit a context token budget.

Pipeline: embed query -> over-fetch from Chroma -> similarity threshold ->
hybrid re-rank (semantic + lexical) -> deduplicate near-identical chunks ->
compress to MAX_CONTEXT_TOKENS -> return top_k.
"""
import re
from dataclasses import dataclass

import tiktoken

from app.core.config import settings
from app.rag.embeddings import embed_query
from app.rag.vectorstore import VectorStore

_ENCODER = tiktoken.get_encoding("cl100k_base")
_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class RetrievedChunk:
    document_id: str
    chunk_id: str
    filename: str
    page_number: int | None
    section_title: str | None
    content: str  # parent-block content, used as generation context
    matched_text: str  # the child chunk that actually matched the query
    similarity_score: float
    lexical_score: float
    hybrid_score: float


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _lexical_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    text_terms = _tokenize(text)
    if not text_terms:
        return 0.0
    overlap = query_terms & text_terms
    return len(overlap) / len(query_terms)


def _jaccard_similarity(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _deduplicate(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Drop chunks whose parent content is near-identical to one already kept."""
    kept: list[RetrievedChunk] = []
    for chunk in chunks:
        if any(_jaccard_similarity(chunk.content, k.content) >= settings.DEDUP_SIMILARITY_THRESHOLD for k in kept):
            continue
        kept.append(chunk)
    return kept


def _compress_to_budget(chunks: list[RetrievedChunk], max_tokens: int) -> list[RetrievedChunk]:
    """Greedily keep highest-ranked chunks until the token budget is exhausted."""
    kept: list[RetrievedChunk] = []
    used = 0
    for chunk in chunks:
        tokens = len(_ENCODER.encode(chunk.content))
        if used + tokens > max_tokens and kept:
            break
        kept.append(chunk)
        used += tokens
    return kept


async def retrieve(
    query: str,
    organization_id: str,
    document_ids: list[str] | None = None,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    top_k = top_k or settings.TOP_K_RESULTS
    query_embedding = await embed_query(query)
    query_terms = _tokenize(query)

    store = VectorStore(organization_id)
    where = {"document_id": {"$in": document_ids}} if document_ids else None
    raw = store.query(query_embedding, top_k=max(top_k * settings.OVER_FETCH_MULTIPLIER, top_k), where=where)

    candidates: list[RetrievedChunk] = []
    if raw["ids"] and raw["ids"][0]:
        for chunk_id, child_text, meta, distance in zip(
            raw["ids"][0], raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
        ):
            similarity = max(0.0, 1 - distance)  # cosine distance -> similarity
            if similarity < settings.SIMILARITY_THRESHOLD:
                continue
            context_text = meta.get("parent_content") or child_text
            lexical = _lexical_score(query_terms, child_text)
            hybrid = settings.SEMANTIC_WEIGHT * similarity + settings.LEXICAL_WEIGHT * lexical
            candidates.append(
                RetrievedChunk(
                    document_id=meta["document_id"],
                    chunk_id=chunk_id,
                    filename=meta.get("filename", "unknown"),
                    page_number=meta.get("page_number") or None,
                    section_title=meta.get("section_title") or None,
                    content=context_text,
                    matched_text=child_text,
                    similarity_score=round(similarity, 4),
                    lexical_score=round(lexical, 4),
                    hybrid_score=round(hybrid, 4),
                )
            )

    candidates.sort(key=lambda c: c.hybrid_score, reverse=True)
    candidates = _deduplicate(candidates)
    candidates = candidates[: top_k * 2]  # keep a small buffer before compression
    candidates = _compress_to_budget(candidates, settings.MAX_CONTEXT_TOKENS)
    return candidates[:top_k]
