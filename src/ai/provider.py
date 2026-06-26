"""Groq / OpenAI orqali javob generatsiyasi."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PROVIDER_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "openai": None,
}


class AIProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        provider: str = "groq",
    ) -> None:
        base_url = PROVIDER_BASE_URLS.get(provider.lower())
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._provider = provider
        self._system_prompt = system_prompt

    async def generate_reply(
        self,
        history: list[dict[str, str]],
        user_message: str,
    ) -> str:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt}
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=400,
                temperature=0.7,
            )
            text = response.choices[0].message.content
            if not text:
                raise ValueError("Empty AI response")
            return text.strip()
        except Exception:
            logger.exception("AI javob generatsiyasi xatolik (%s)", self._provider)
            raise
