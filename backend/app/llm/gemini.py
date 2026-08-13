"""Gemini implementation of LLMProvider. Chat generation ONLY -- no embeddings here."""
from typing import AsyncGenerator

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging_config import logger
from app.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        # Re-read settings each time so .env updates after process start are picked up
        # when the provider singleton was created before the key was set.
        api_key = (settings.GEMINI_API_KEY or "").strip()
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file to enable chat generation "
                "(get a free key at https://aistudio.google.com/apikey)."
            )
        if self._client is None:
            self._client = genai.Client(api_key=api_key)
        return self._client

    async def stream_chat(
        self, system_prompt: str, history: list[dict], user_message: str
    ) -> AsyncGenerator[str, None]:
        try:
            client = self._get_client()
        except RuntimeError as exc:
            logger.error(str(exc))
            yield (
                "Chat is not configured yet. Set `GEMINI_API_KEY` in `backend/.env` "
                "(free key: https://aistudio.google.com/apikey), then restart the backend."
            )
            return

        contents = [
            types.Content(role=turn["role"], parts=[types.Part.from_text(text=turn["text"])]) for turn in history
        ]
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        config = types.GenerateContentConfig(
            system_instruction=system_prompt[:12000],
            temperature=0.3,
            max_output_tokens=1024,
        )

        try:
            stream = client.aio.models.generate_content_stream(
                model=settings.GEMINI_CHAT_MODEL, contents=contents, config=config
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:  # pragma: no cover - network/SDK errors
            logger.error(f"Gemini streaming error: {exc}")
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                yield (
                    "Gemini quota exceeded for this API key/model. "
                    f"Try another model (current: `{settings.GEMINI_CHAT_MODEL}`) "
                    "or wait and retry. Details: https://ai.google.dev/gemini-api/docs/rate-limits"
                )
            elif "401" in msg or "403" in msg or "UNAUTHENTICATED" in msg or "PERMISSION" in msg.upper():
                yield "Gemini rejected the API key. Check `GEMINI_API_KEY` in `backend/.env`."
            elif "404" in msg or "NOT_FOUND" in msg:
                yield (
                    f"Model `{settings.GEMINI_CHAT_MODEL}` is not available for this key. "
                    "Set `GEMINI_CHAT_MODEL` in `backend/.env` to a supported model "
                    "(e.g. `gemini-flash-latest`)."
                )
            else:
                yield "\n\n_[An error occurred while generating the response. Please try again.]_"
