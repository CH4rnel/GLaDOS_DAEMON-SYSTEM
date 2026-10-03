# ♃ ☿  OMNISSIAH CODE LAYER  ☿ ♃

"""
Base class for OpenAI-wire-compatible LLM providers.
"""

import httpx
import json
from typing import AsyncGenerator
from loguru import logger

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
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0,
        )
        self.logger = logger.bind(provider=profile.provider.value, agent=profile.agent_id)

    def _get_client(self) -> httpx.AsyncClient:
        """Returns the underlying HTTP client. Primarily exposed for unit testing/mocking."""
        return self._client

    async def complete(self, messages: list[LLMMessage], **kw) -> LLMResponse:
        client = self._get_client()
        payload = {
            "model": kw.get("model", self.profile.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        
        # Include max_tokens if specified in profile or kwargs
        max_tokens = kw.get("max_tokens") or self.profile.max_tokens
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Include other optional parameters
        if self.profile.temperature is not None:
            payload["temperature"] = kw.get("temperature", self.profile.temperature)
        
        self.logger.debug(f"Sending request to /chat/completions with model: {payload['model']}, max_tokens: {payload.get('max_tokens', 'default')}")
        
        try:
            resp = await client.post("/chat/completions", json=payload)
            self.logger.debug(f"Response status: {resp.status_code}")
            
            if resp.status_code != 200:
                error_text = resp.text
                self.logger.error(f"API error {resp.status_code}: {error_text}")
                raise Exception(f"API error {resp.status_code}: {error_text}")
            
            data = resp.json()
            return LLMResponse(content=data["choices"][0]["message"]["content"])
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP status error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise

    async def complete_stream(self, messages: list[LLMMessage], profile: AgentProfile) -> AsyncGenerator[str, None]:
        client = self._get_client()
        payload = {
            "model": profile.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        
        # Include max_tokens if specified in profile
        if profile.max_tokens:
            payload["max_tokens"] = profile.max_tokens
        
        # Include temperature if specified
        if profile.temperature is not None:
            payload["temperature"] = profile.temperature
        
        self.logger.debug(f"Starting stream with model: {profile.model}, max_tokens: {payload.get('max_tokens', 'default')}")
        
        try:
            async with client.stream("POST", "/chat/completions", json=payload) as resp:
                self.logger.debug(f"Stream response status: {resp.status_code}")
                
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    self.logger.error(f"Stream error {resp.status_code}: {error_text}")
                    raise Exception(f"Stream error {resp.status_code}: {error_text}")
                
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse chunk: {e}, data: {data}")
                            continue
                            
        except httpx.HTTPStatusError as e:
            error_body = await e.response.aread()
            self.logger.error(f"HTTP stream error {e.response.status_code}: {error_body}")
            raise
        except Exception as e:
            self.logger.error(f"Stream failed: {e}")
            raise

    async def validate_api_key(self) -> bool:
        try:
            resp = await self._client.get("/models")
            self.logger.debug(f"Validation response: {resp.status_code}")
            return resp.status_code == 200
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False