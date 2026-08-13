"""
ChromaDB-backed vector store, isolated per organization (multi-tenant).
A thin abstraction (add / query / delete) keeps the rest of the codebase
unaware it's Chroma specifically -- FAISS or Pinecone could be swapped in
here by implementing the same three methods.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

_chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=ChromaSettings(anonymized_telemetry=False),
)


def _collection_name(organization_id: str) -> str:
    return f"{settings.CHROMA_COLLECTION_PREFIX}_{organization_id}".replace("-", "")


class VectorStore:
    def __init__(self, organization_id: str):
        self.collection = _chroma_client.get_or_create_collection(
            name=_collection_name(organization_id),
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]) -> None:
        self.collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, embedding: list[float], top_k: int, where: dict | None = None) -> dict:
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def delete_by_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})
