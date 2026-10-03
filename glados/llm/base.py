# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base LLM Provider interface for GLaDOS.
All provider implementations must conform to this contract.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from glados.llm.models import AgentProfile, LLMMessage, LLMResponse

class BaseLLMProvider(ABC):
    def __init__(self, profile: AgentProfile) -> None:
        self.profile = profile

    @abstractmethod
    async def complete(self, messages: list[LLMMessage], **kw) -> LLMResponse:
        pass

    @abstractmethod
    async def complete_stream(self, messages: list[LLMMessage], profile: AgentProfile) -> AsyncGenerator[str, None]:
        pass

    async def validate_api_key(self) -> bool:
        """Default validation: attempts a lightweight API call."""
        return False