"""
Two-tier (parent/child) recursive chunking with overlap.

Why parent/child: small chunks give precise embedding similarity, but
returning only a 150-token fragment to the LLM often lacks context. So we
chunk twice -- large "parent" blocks (~3x child size) for context, and small
"child" chunks within each parent for the actual vector search. Retrieval
matches on children; generation context uses the parent block they belong to.
"""
import re
from dataclasses import dataclass, field

import tiktoken

from app.core.config import settings

_ENCODER = tiktoken.get_encoding("cl100k_base")

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
PARENT_SIZE_MULTIPLIER = 3


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_number: int | None
    token_count: int
    parent_index: int
    parent_content: str
    section_title: str | None = field(default=None)


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def _split_recursive(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if not text.strip():
        return []

    if _count_tokens(text) <= chunk_size:
        return [text]

    if not separators:
        words = text.split()
        if len(words) <= 1:
            return [text]
        mid = len(words) // 2
        return _split_recursive(" ".join(words[:mid]), [], chunk_size) + _split_recursive(
            " ".join(words[mid:]), [], chunk_size
        )

    sep, rest = separators[0], separators[1:]
    parts = text.split(sep) if sep else list(text)
    if len(parts) == 1:
        return _split_recursive(text, rest, chunk_size)

    chunks, buffer = [], ""
    for part in parts:
        candidate = buffer + sep + part if buffer else part
        if _count_tokens(candidate) <= chunk_size:
            buffer = candidate
        else:
            if buffer:
                chunks.extend(_split_recursive(buffer, rest, chunk_size) if _count_tokens(buffer) > chunk_size else [buffer])
            buffer = part
    if buffer:
        chunks.extend(_split_recursive(buffer, rest, chunk_size) if _count_tokens(buffer) > chunk_size else [buffer])

    if not chunks:
        words = text.split()
        if len(words) <= 1:
            return [text]
        mid = len(words) // 2
        return _split_recursive(" ".join(words[:mid]), [], chunk_size) + _split_recursive(
            " ".join(words[mid:]), [], chunk_size
        )
    return [c for c in chunks if c.strip()]


def _add_overlap(chunks: list[str], overlap_tokens: int) -> list[str]:
    if overlap_tokens <= 0 or len(chunks) <= 1:
        return chunks
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tokens = _ENCODER.encode(chunks[i - 1])
        overlap_text = _ENCODER.decode(prev_tokens[-overlap_tokens:]) if len(prev_tokens) > overlap_tokens else chunks[i - 1]
        result.append((overlap_text + " " + chunks[i]).strip())
    return result


def _extract_section_title(block: str) -> str | None:
    """Lightweight metadata extraction: treat a short first line as a heading."""
    first_line = block.strip().split("\n", 1)[0].strip()
    if 0 < len(first_line) <= 90 and not first_line.endswith((".", ",", ";")):
        return first_line
    return None


def chunk_pages(pages: list[tuple[str, int | None]]) -> list[TextChunk]:
    """Chunk each (text, page_number) pair into parent blocks, then child chunks within each."""
    all_chunks: list[TextChunk] = []
    idx = 0
    parent_idx = 0

    for text, page_number in pages:
        text = re.sub(r"\s+\n", "\n", text).strip()
        if not text:
            continue

        parent_blocks = _split_recursive(text, SEPARATORS, settings.CHUNK_SIZE * PARENT_SIZE_MULTIPLIER)
        for parent_block in parent_blocks:
            section_title = _extract_section_title(parent_block)
            child_raw = _split_recursive(parent_block, SEPARATORS, settings.CHUNK_SIZE)
            child_raw = _add_overlap(child_raw, settings.CHUNK_OVERLAP)
            for c in child_raw:
                all_chunks.append(
                    TextChunk(
                        content=c.strip(),
                        chunk_index=idx,
                        page_number=page_number,
                        token_count=_count_tokens(c),
                        parent_index=parent_idx,
                        parent_content=parent_block.strip(),
                        section_title=section_title,
                    )
                )
                idx += 1
            parent_idx += 1

    return all_chunks
