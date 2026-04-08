# pyright: reportMissingImports=false

from __future__ import annotations

from app.config import get_settings
from app.core.exceptions import ServiceUnavailableError


class LLMProvider:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _client_and_model(self):
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ServiceUnavailableError("openai package is not installed.", code="llm_client_unavailable") from exc

        provider = self._settings.llm_provider.lower().strip()

        if provider == "openai":
            if not self._settings.openai_api_key:
                raise ServiceUnavailableError("OpenAI provider is not configured.", code="llm_not_configured")
            return AsyncOpenAI(api_key=self._settings.openai_api_key), self._settings.openai_model

        if not self._settings.gemini_api_key:
            raise ServiceUnavailableError("Gemini provider is not configured.", code="llm_not_configured")

        client = AsyncOpenAI(
            api_key=self._settings.gemini_api_key,
            base_url=self._settings.gemini_base_url,
        )
        return client, self._settings.gemini_model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        client, model = self._client_and_model()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=self._settings.response_max_tokens,
        )
        message = response.choices[0].message.content
        return message or "No answer generated."
