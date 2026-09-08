# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
OpenAI LLM Provider implementation for GLaDOS_DAEMON-SYSTEM.
Provides integration with OpenAI API and compatible endpoints (e.g., OpenRouter, Azure).
"""

from typing import Any

import httpx
from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse, ProviderType


class OpenAIProvider(BaseLLMProvider):
    """
    Provider implementation for OpenAI-compatible APIs.
    Supports GPT-4, o1, and other models via standard /v1/chat/completions endpoint.
    """

    def __init__(self, timeout: float = 60.0, default_base_url: str = "https://api.openai.com/v1") -> None:
        """
        Initialize the OpenAI provider.
        
        :param timeout: Default timeout for HTTP requests in seconds.
        :param default_base_url: Default API endpoint (allows overriding for OpenRouter, etc.).
        """
        self.timeout = timeout
        self.default_base_url = default_base_url
        self.logger = logger.bind(component="OpenAIProvider")

    async def complete(
        self, 
        messages: list[LLMMessage], 
        profile: AgentProfile
    ) -> LLMResponse:
        """
        Send messages to OpenAI API and get a response.
        
        :param messages: List of conversation messages.
        :param profile: Agent profile with model and connection details.
        :return: Structured LLMResponse.
        """
        if not profile.api_key:
            error_msg = "Error: api_key is required for OpenAI provider."
            self.logger.error(error_msg)
            return LLMResponse(
                content=error_msg,
                model=profile.model,
                provider=ProviderType.OPENAI,
                is_error=True,
                metadata={"error": "Missing API Key"}
            )

        base_url = profile.base_url or self.default_base_url
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {profile.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = self._build_payload(messages, profile)
        
        self.logger.debug(
            f"Sending request to OpenAI: model={profile.model}, "
            f"endpoint={endpoint}, messages_count={len(messages)}"
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_response(data, profile)
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            self.logger.error(f"OpenAI API error: {error_msg}")
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.OPENAI,
                is_error=True,
                metadata={
                    "error": f"HTTP {e.response.status_code}",
                    "details": e.response.text
                }
            )
        except httpx.ConnectError as e:
            error_msg = f"Connection failed: {str(e)}"
            self.logger.error(f"Cannot connect to OpenAI at {base_url}: {e}")
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.OPENAI,
                is_error=True,
                metadata={
                    "error": "Connection failed",
                    "details": str(e)
                }
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error in OpenAIProvider: {e}", exc_info=True)
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.OPENAI,
                is_error=True,
                metadata={
                    "error": "Unexpected error",
                    "details": str(e)
                }
            )

    async def health_check(self, profile: AgentProfile) -> bool:
        """
        Check if OpenAI API is available and responsive.
        Pings the /models endpoint.
        
        :param profile: Agent profile with connection details.
        :return: True if healthy, False otherwise.
        """
        if not profile.api_key:
            return False

        base_url = profile.base_url or self.default_base_url
        endpoint = f"{base_url.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {profile.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(endpoint, headers=headers)
                response.raise_for_status()
                return True
        except Exception as e:
            self.logger.warning(f"OpenAI health check failed: {e}")
            return False

    def _build_payload(
        self, 
        messages: list[LLMMessage], 
        profile: AgentProfile
    ) -> dict[str, Any]:
        """
        Build the complete payload for OpenAI API request.
        
        :param messages: List of message objects.
        :param profile: Agent profile with model and options.
        :return: Complete request payload.
        """
        payload: dict[str, Any] = {
            "model": profile.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages]
        }
        
        if profile.temperature is not None:
            payload["temperature"] = profile.temperature
        
        if profile.max_tokens is not None:
            payload["max_tokens"] = profile.max_tokens
        
        return payload

    def _parse_response(self, data: dict[str, Any], profile: AgentProfile) -> LLMResponse:
        """
        Parse OpenAI API response into LLMResponse.
        
        :param data: Raw response data from OpenAI API.
        :param profile: Agent profile used for the request.
        :return: Structured LLMResponse.
        """
        choices = data.get("choices", [])
        content = ""
        if choices and "message" in choices[0]:
            content = choices[0]["message"].get("content", "")
        
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            model=data.get("model", profile.model),
            provider=ProviderType.OPENAI,
            usage=usage,
            metadata={
                "finish_reason": choices[0].get("finish_reason", "unknown") if choices else "unknown",
                "id": data.get("id", "")
            }
        )