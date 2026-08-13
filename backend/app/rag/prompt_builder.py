"""Builds the grounded system prompt from retrieved chunks, plus post-hoc citation verification."""
from app.core.config import settings
from app.rag.retriever import RetrievedChunk

SYSTEM_TEMPLATE = """You are an enterprise knowledge assistant. Answer the user's question \
using ONLY the context below, which was retrieved from their uploaded documents.

Rules:
- If the answer is not contained in the context, say you don't have enough information -- \
never fabricate an answer.
- Always be concise and precise.
- When you use a fact from a source, mention which document it came from in prose \
(e.g. "According to <filename> ...").
- If sources disagree, point that out explicitly.

CONTEXT:
{context}
"""


def build_system_prompt(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return (
            "You are an enterprise knowledge assistant. No relevant context was found in the "
            "user's documents for this question. Tell the user you couldn't find relevant "
            "information in their uploaded documents, and ask them to rephrase or upload more context."
        )
    context_blocks = []
    for i, c in enumerate(chunks, start=1):
        page_info = f", page {c.page_number}" if c.page_number else ""
        section_info = f" ({c.section_title})" if c.section_title else ""
        context_blocks.append(f"[Source {i}: {c.filename}{page_info}{section_info}]\n{c.content}")
    return SYSTEM_TEMPLATE.format(context="\n\n---\n\n".join(context_blocks))


def verify_citations(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """
    Lightweight citation verification: drops any chunk below the similarity
    threshold (already filtered upstream, kept here as a safety net) and
    collapses duplicate (document, page) citations down to their
    highest-scoring occurrence, so the same page isn't cited twice.
    """
    best_per_source: dict[tuple[str, int | None], RetrievedChunk] = {}
    for c in chunks:
        if c.similarity_score < settings.SIMILARITY_THRESHOLD:
            continue
        key = (c.document_id, c.page_number)
        existing = best_per_source.get(key)
        if existing is None or c.hybrid_score > existing.hybrid_score:
            best_per_source[key] = c
    return sorted(best_per_source.values(), key=lambda c: c.hybrid_score, reverse=True)


def build_citations(chunks: list[RetrievedChunk]) -> list[dict]:
    verified = verify_citations(chunks)
    return [
        {
            "document_id": c.document_id,
            "chunk_id": c.chunk_id,
            "filename": c.filename,
            "page_number": c.page_number,
            "section_title": c.section_title,
            "chunk_text": c.matched_text[:300],
            "similarity_score": c.similarity_score,
            "confidence_score": round(c.hybrid_score, 4),
        }
        for c in verified
    ]


def average_confidence(chunks: list[RetrievedChunk]) -> float | None:
    if not chunks:
        return None
    return round(sum(c.hybrid_score for c in chunks) / len(chunks), 4)
