"""
Abstract interface every chat-generation provider must implement. Embeddings
are deliberately NOT part of this interface -- they always run locally via
app/rag/embeddings.py regardless of which LLM provider generates text.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, system_prompt: str, history: list[dict], user_message: str
    ) -> AsyncGenerator[str, None]:
        """Yields response text incrementally (token/chunk by chunk)."""
        raise NotImplementedError
