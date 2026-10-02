# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base class for OpenAI-wire-compatible LLM providers.
"""

import httpx
import json
from typing import AsyncGenerator

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse


class OpenAICompatibleProvider(BaseLLMProvider):
    """Base for any OpenAI-wire-compatible endpoint."""
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, profile: AgentProfile) -> None:
        self.profile = profile
        api_key = profile.api_key.get_secret_value() if profile.api_key else ""
        base_url = profile.base_url or self.DEFAULT_BASE_URL
        
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    def _get_client(self) -> httpx.AsyncClient:
        """Returns the underlying HTTP client. Primarily exposed for unit testing/mocking."""
        return self._client

    async def complete(self, messages: list[LLMMessage], **kw) -> LLMResponse:
        client = self._get_client()
        resp = await client.post("/chat/completions", json={
            "model": kw.get("model", self.profile.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **{k: v for k, v in kw.items() if k != "model"},
        })
        resp.raise_for_status()
        data = resp.json()
        return LLMResponse(content=data["choices"][0]["message"]["content"])

    async def complete_stream(self, messages: list[LLMMessage], profile: AgentProfile) -> AsyncGenerator[str, None]:
        client = self._get_client()
        payload = {
            "model": profile.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        async with client.stream("POST", "/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue