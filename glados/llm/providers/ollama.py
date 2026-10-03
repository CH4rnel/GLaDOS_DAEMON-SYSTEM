# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Ollama provider implementation with streaming support via REST API.
Uses httpx (already a transitive dependency) instead of aiohttp to keep the dependency tree clean.
"""

import json
from typing import AsyncIterator
import httpx
from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """Provider for local Ollama models."""

    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.base_url = profile.base_url or "http://localhost:11434"
        self._client: httpx.AsyncClient | None = None
        self.logger = logger.bind(component="OllamaProvider", model=profile.model)

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy initialization of httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        return self._client

    async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
        """Execute single completion request via Ollama REST API."""
        client = self._get_client()
        payload = {
            "model": profile.model,
            "messages": self._format_messages(messages, profile.system_prompt),
            "stream": False,
            "options": {"temperature": profile.temperature or 0.7},
        }

        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data.get("message", {}).get("content", "")
        self.logger.debug(f"Ollama response: {len(content)} chars")

        return LLMResponse(
            content=content,
            model=profile.model,
            usage={"input_tokens": 0, "output_tokens": 0},
        )

    async def complete_stream(self, messages: list[LLMMessage], profile: AgentProfile) -> AsyncIterator[str]:
        """Stream completion via Ollama REST API stream endpoint."""
        client = self._get_client()
        payload = {
            "model": profile.model,
            "messages": self._format_messages(messages, profile.system_prompt),
            "stream": True,
            "options": {"temperature": profile.temperature or 0.7},
        }

        async with client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    def _format_messages(self, messages: list[LLMMessage], system_prompt: str | None) -> list[dict]:
        """Convert LLMMessage list to Ollama message format."""
        conversation = []
        if system_prompt:
            conversation.append({"role": "system", "content": system_prompt})
        for msg in messages:
            conversation.append({"role": msg.role, "content": msg.content})
        return conversation

    async def validate_api_key(self) -> bool:
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False