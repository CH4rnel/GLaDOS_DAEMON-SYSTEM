# glados/llm/providers/ollama.py — full file
# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Ollama LLM Provider implementation for GLaDOS_DAEMON-SYSTEM.
Provides integration with local Ollama API for running open-source LLMs.

Network hardening: same rationale as glados/llm/providers/openai.py —
`trust_env=False` so ambient HTTP_PROXY/HTTPS_PROXY env vars are ignored,
with an explicit `egress_proxy` opt-in instead. Ollama is usually local
(http://localhost:11434) so this matters less than for cloud providers,
but if `base_url` is ever pointed at a remote Ollama instance, the same
malicious-intermediary risk applies.
"""

import os
from typing import Any

import httpx
from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse, ProviderType


class OllamaProvider(BaseLLMProvider):
    """
    Provider implementation for Ollama API.
    Supports local execution of open-source models (Llama, Qwen, Mistral, etc.).
    """

    def __init__(self, timeout: float = 120.0, egress_proxy: str | None = None) -> None:
        """
        Initialize the Ollama provider.

        :param timeout: Default timeout for HTTP requests in seconds.
        :param egress_proxy: If set (or GLADOS_EGRESS_PROXY env var is set),
            requests are routed through this proxy instead of picking up
            ambient environment proxy settings.
        """
        self.timeout = timeout
        self.egress_proxy = egress_proxy or os.environ.get("GLADOS_EGRESS_PROXY")
        self.logger = logger.bind(component="OllamaProvider")

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
        Send messages to Ollama and get a response.
        
        :param messages: List of conversation messages.
        :param profile: Agent profile with model and connection details.
        :return: Structured LLMResponse.
        """
        base_url = profile.base_url or "http://localhost:11434"
        endpoint = f"{base_url.rstrip('/')}/api/chat"
        
        # Build request payload
        request_messages = self._build_messages(messages, profile)
        payload = self._build_payload(request_messages, profile)
        
        self.logger.debug(
            f"Sending request to Ollama: model={profile.model}, "
            f"messages_count={len(request_messages)}"
        )
        
        try:
            async with self._client() as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                
                data = response.json()
                return self._parse_response(data, profile)
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            self.logger.error(f"Ollama API error: {error_msg}")
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.OLLAMA,
                is_error=True,
                metadata={
                    "error": f"HTTP {e.response.status_code}",
                    "details": e.response.text
                }
            )
        except httpx.ConnectError as e:
            error_msg = f"Connection failed: {str(e)}"
            self.logger.error(f"Cannot connect to Ollama at {base_url}: {e}")
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.OLLAMA,
                is_error=True,
                metadata={
                    "error": "Connection failed",
                    "details": str(e)
                }
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error in OllamaProvider: {e}", exc_info=True)
            return LLMResponse(
                content=f"Error: {error_msg}",
                model=profile.model,
                provider=ProviderType.OLLAMA,
                is_error=True,
                metadata={
                    "error": "Unexpected error",
                    "details": str(e)
                }
            )

    async def health_check(self, profile: AgentProfile) -> bool:
        """
        Check if Ollama API is available and responsive.
        
        :param profile: Agent profile with connection details.
        :return: True if healthy, False otherwise.
        """
        base_url = profile.base_url or "http://localhost:11434"
        endpoint = f"{base_url.rstrip('/')}/api/tags"
        
        try:
            async with httpx.AsyncClient(
                timeout=5.0, proxy=self.egress_proxy, trust_env=False
            ) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                return True
        except Exception as e:
            self.logger.warning(f"Ollama health check failed: {e}")
            return False

    def _build_messages(
        self, 
        messages: list[LLMMessage], 
        profile: AgentProfile
    ) -> list[dict[str, str]]:
        """
        Build the messages array for Ollama API request.
        Includes system prompt from profile if present.
        
        :param messages: List of conversation messages.
        :param profile: Agent profile with system prompt.
        :return: List of message dictionaries.
        """
        result = []
        
        # Add system prompt if present in profile
        if profile.system_prompt:
            result.append({
                "role": "system",
                "content": profile.system_prompt
            })
        
        # Add conversation messages
        for msg in messages:
            result.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return result

    def _build_payload(
        self, 
        messages: list[dict[str, str]], 
        profile: AgentProfile
    ) -> dict[str, Any]:
        """
        Build the complete payload for Ollama API request.
        
        :param messages: List of message dictionaries.
        :param profile: Agent profile with model and options.
        :return: Complete request payload.
        """
        payload: dict[str, Any] = {
            "model": profile.model,
            "messages": messages,
            "stream": False
        }
        
        # Add generation options
        options: dict[str, Any] = {}
        
        if profile.temperature is not None:
            options["temperature"] = profile.temperature
        
        if profile.max_tokens is not None:
            options["num_predict"] = profile.max_tokens
        
        if options:
            payload["options"] = options
        
        return payload

    def _parse_response(self, data: dict[str, Any], profile: AgentProfile) -> LLMResponse:
        """
        Parse Ollama API response into LLMResponse.
        
        :param data: Raw response data from Ollama API.
        :param profile: Agent profile used for the request.
        :return: Structured LLMResponse.
        """
        message = data.get("message", {})
        content = message.get("content", "")
        
        # Extract usage statistics
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        }
        
        # Extract metadata
        metadata = {
            "done": data.get("done", False),
            "total_duration": data.get("total_duration", 0),
            "load_duration": data.get("load_duration", 0),
            "eval_duration": data.get("eval_duration", 0)
        }
        
        return LLMResponse(
            content=content,
            model=data.get("model", profile.model),
            provider=ProviderType.OLLAMA,
            usage=usage,
            metadata=metadata
        )