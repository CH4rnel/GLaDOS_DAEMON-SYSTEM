# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base interfaces for the GLaDOS LLM subsystem.
Defines the abstract contracts that all LLM providers and agents must implement.
"""

from abc import ABC, abstractmethod

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