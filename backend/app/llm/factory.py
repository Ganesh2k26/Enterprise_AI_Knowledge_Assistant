"""
Provider factory: selects the active LLMProvider from settings.LLM_PROVIDER
(env var `LLM_PROVIDER`). Adding a new provider means implementing
LLMProvider in a new file and registering it in `_PROVIDERS` -- no other
code in the app needs to change.
"""
from functools import lru_cache

from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.gemini import GeminiProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "gemini": GeminiProvider,
    # "openai": OpenAIProvider,      # add here to support another free/paid provider
    # "anthropic": AnthropicProvider,
}


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider_cls = _PROVIDERS.get(settings.LLM_PROVIDER)
    if provider_cls is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. Available: {list(_PROVIDERS)}"
        )
    return provider_cls()
