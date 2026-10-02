# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base LLM Provider interface for GLaDOS.
All provider implementations must conform to this contract.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM provider implementations."""

    @abstractmethod
    async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
        """
        Execute a single completion request and return the full response.
        
        :param messages: List of conversation messages.
        :param profile: Agent profile with model and configuration.
        :return: Complete LLM response.
        """
        pass

    async def complete_stream(self, messages: list[LLMMessage], profile: AgentProfile) -> AsyncIterator[str]:
        """
        Stream completion response as async generator yielding text chunks.
        Default implementation falls back to complete() and yields the full content as single chunk.
        Providers with native streaming support should override this method.
        
        :param messages: List of conversation messages.
        :param profile: Agent profile with model and configuration.
        :yields: Text chunks as they are generated.
        """
        response = await self.complete(messages, profile)
        yield response.content