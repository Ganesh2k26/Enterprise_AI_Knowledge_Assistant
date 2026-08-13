from app.rag.chunking import chunk_pages


def test_chunk_pages_basic():
    text = "This is a sentence. " * 200
    chunks = chunk_pages([(text, 1)])
    assert len(chunks) > 1
    assert all(c.page_number == 1 for c in chunks)
    assert all(c.token_count > 0 for c in chunks)


def test_chunk_pages_empty():
    assert chunk_pages([("   ", None)]) == []
