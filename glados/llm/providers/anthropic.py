# ♃ ☿  OMNISSIAH CODE LAYER  ☿ ♃

"""
Anthropic Claude provider implementation with streaming support.
"""

from typing import AsyncIterator
from anthropic import AsyncAnthropic
from loguru import logger

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self._client: AsyncAnthropic | None = None
        self.logger = logger.bind(component="AnthropicProvider", model=profile.model)

    def _get_client(self) -> AsyncAnthropic:
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            api_key = self.profile.api_key.get_secret_value() if self.profile.api_key else None
            self._client = AsyncAnthropic(api_key=api_key)
        return self._client

    async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
        """Execute single completion request."""
        client = self._get_client()

        system_prompt = profile.system_prompt or ""
        conversation = self._format_messages(messages)

        response = await client.messages.create(
            model=profile.model,
            max_tokens=profile.max_tokens or 4096,
            system=system_prompt,
            messages=conversation,
            temperature=profile.temperature or 0.7,
        )

        content = response.content[0].text if response.content else ""
        self.logger.debug(f"Anthropic response: {len(content)} chars")

        return LLMResponse(
            content=content,
            model=profile.model,
            usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
        )

    async def complete_stream(self, messages: list[LLMMessage], profile: AgentProfile) -> AsyncIterator[str]:
        """Stream completion via Anthropic messages.stream()."""
        client = self._get_client()

        system_prompt = profile.system_prompt or ""
        conversation = self._format_messages(messages)

        async with client.messages.stream(
            model=profile.model,
            max_tokens=profile.max_tokens or 4096,
            system=system_prompt,
            messages=conversation,
            temperature=profile.temperature or 0.7,
        ) as stream:
            async for text_delta in stream.text_stream:
                yield text_delta

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessage list to Anthropic message format."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]