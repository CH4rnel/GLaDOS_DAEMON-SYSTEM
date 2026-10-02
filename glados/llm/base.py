# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base interfaces for the GLaDOS LLM subsystem.
Defines the abstract contracts that all LLM providers and agents must implement.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from loguru import logger
from glados.llm.models import AgentProfile, LLMMessage, LLMResponse


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM provider implementations.
    A provider handles the low-level transport and API-specific logic 
    for communicating with a specific LLM service (e.g., Ollama, OpenAI).
    """

    @abstractmethod
    async def complete(
        self, 
        messages: list[LLMMessage], 
        profile: AgentProfile
    ) -> LLMResponse:
        """
        Sends a list of messages to the LLM and returns a single response.
        
        :param messages: The conversation history.
        :param profile: The agent profile containing model and connection details.
        :return: A structured LLMResponse.
        """
        pass

    @abstractmethod
    async def health_check(self, profile: AgentProfile) -> bool:
        """
        Checks if the provider and the specific model are reachable and responsive.
        
        :param profile: The agent profile to check.
        :return: True if healthy, False otherwise.
        """
        pass

    """
    BrainEngine orchestration layer.
    Routes messages through LLMRouter and supports streaming responses.
    """
class BrainEngine:
    """
    Core reasoning engine that interfaces with the LLM fleet.
    """

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        logger.debug(f"BrainEngine initialized for agent: {agent_id}")

    async def process_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Yields chunks of the LLM response for WebSocket streaming.
        In production, this routes through LLMRouter to the selected provider.
        """
        # Stub implementation for TDD green phase
        # Real implementation will invoke LLMRouter.stream()
        yield "Thinking..."
        yield "Done."