# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Anthropic Claude LLM Provider implementation for GLaDOS_DAEMON-SYSTEM.
Provides integration with Anthropic Messages API.

Network hardening notes:
- `trust_env=False` on the httpx client: prevents ambient proxy configuration
- `egress_proxy` support for audited egress routing
- System prompt extraction: Anthropic API requires system prompt as separate parameter
"""

import os
from typing import Any

import httpx
from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse, ProviderType


class AnthropicProvider(BaseLLMProvider):
    """
    Provider implementation for Anthropic Claude API.
    Uses Messages API endpoint with proper system prompt handling.
    """

    def __init__(
        self,
        timeout: float = 60.0,
        egress_proxy: str | None = None,
    ) -> None:
        """
        Initialize the Anthropic provider.

        :param timeout: Default timeout for HTTP requests in seconds.
        :param egress_proxy: If set (or if GLADOS_EGRESS_PROXY is set), 
            all requests are routed through this proxy.
        """
        self.timeout = timeout
        self.egress_proxy = egress_proxy or os.environ.get("GLADOS_EGRESS_PROXY")
        self.logger = logger.bind(component="AnthropicProvider")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self.timeout,
            proxy=self.egress_proxy,
            trust_env=False,
        )

    async def complete(
        self, 
        messages: list[LLMMessage], 
        profile: AgentProfile
    ) -> LLMResponse:
        """
        Send messages to Anthropic API and get a response.
        
        :param messages: List of conversation messages.
        :param profile: Agent profile with model and connection details.
        :return: Structured LLMResponse.
        """
        if not profile.api_key:
            error_msg = "Error: api_key is required for Anthropic provider."
            self.logger.error(error_msg)
            return LLMResponse(
                content=error_msg,
                model=profile.model,
                provider=ProviderType.ANTHROPIC,
                is_error=True,
                metadata={"error": "Missing API Key"}
            )

        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": profile.api_key.get_secret_value(),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = self._build_payload(messages, profile)
        
        self.logger.debug(
            f"Sending request to Anthropic: model={profile.model}, "
            f"messages_count={len(messages)}"
        )
        
        try:
            async with self._client() as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_response(data, profile)
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            self.logger.error(f"Anthropic API error: {error_msg}")
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.ANTHROPIC,
                is_error=True,
                metadata={
                    "error": f"HTTP {e.response.status_code}",
                    "details": e.response.text
                }
            )
        except httpx.ConnectError as e:
            error_msg = f"Connection failed: {str(e)}"
            self.logger.error(f"Cannot connect to Anthropic: {e}")
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.ANTHROPIC,
                is_error=True,
                metadata={
                    "error": "Connection failed",
                    "details": str(e)
                }
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error in AnthropicProvider: {e}", exc_info=True)
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.ANTHROPIC,
                is_error=True,
                metadata={
                    "error": "Unexpected error",
                    "details": str(e)
                }
            )

    async def health_check(self, profile: AgentProfile) -> bool:
        """
        Check if Anthropic API is available and responsive.
        Sends minimal request to verify connectivity.
        
        :param profile: Agent profile with connection details.
        :return: True if healthy, False otherwise.
        """
        if not profile.api_key:
            return False

        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": profile.api_key.get_secret_value(),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=5.0, proxy=self.egress_proxy, trust_env=False
            ) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json={
                        "model": profile.model,
                        "messages": [{"role": "user", "content": "."}],
                        "max_tokens": 1
                    }
                )
                return response.status_code in (200, 400)
        except Exception as e:
            self.logger.warning(f"Anthropic health check failed: {e}")
            return False

    def _build_payload(
        self, 
        messages: list[LLMMessage], 
        profile: AgentProfile
    ) -> dict[str, Any]:
        """
        Build the payload for Anthropic API request.
        Extracts system prompt to separate field per Anthropic requirements.
        
        :param messages: List of message objects.
        :param profile: Agent profile with model and options.
        :return: Complete request payload.
        """
        system_prompt = ""
        filtered_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_prompt += msg.content + "\n"
            else:
                filtered_messages.append({"role": msg.role, "content": msg.content})

        payload: dict[str, Any] = {
            "model": profile.model,
            "messages": filtered_messages,
            "max_tokens": profile.max_tokens or 4096
        }
        
        if system_prompt.strip():
            payload["system"] = system_prompt.strip()
        
        if profile.temperature is not None:
            payload["temperature"] = profile.temperature
        
        return payload

    def _parse_response(self, data: dict[str, Any], profile: AgentProfile) -> LLMResponse:
        """
        Parse Anthropic API response into LLMResponse.
        
        :param data: Raw response data from Anthropic API.
        :param profile: Agent profile used for the request.
        :return: Structured LLMResponse.
        """
        content_blocks = data.get("content", [])
        text_content = ""
        tool_calls = []
        
        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(block)

        if not text_content and tool_calls:
            text_content = "[Tool calls executed]"

        usage = data.get("usage", {})
        
        return LLMResponse(
            content=text_content,
            model=data.get("model", profile.model),
            provider=ProviderType.ANTHROPIC,
            usage=usage,
            metadata={
                "stop_reason": data.get("stop_reason", "unknown"),
                "id": data.get("id", "")
            }
        )