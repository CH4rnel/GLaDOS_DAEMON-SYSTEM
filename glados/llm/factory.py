# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
LLM Provider Factory for GLaDOS_DAEMON-SYSTEM.
Dynamically instantiates the correct LLM provider based on AgentProfile configuration.
Follows the Factory design pattern to maintain loose coupling and SOLID principles.
"""

from glados.llm.base import BaseLLMProvider
from glados.llm.models import AgentProfile, ProviderType
from glados.llm.providers.openai import OpenAIProvider
from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.anthropic import AnthropicProvider


class LLMProviderFactory:
    """
    Factory class responsible for creating LLM provider instances.
    Centralizes provider instantiation logic and ensures type safety.
    """

    @staticmethod
    def create_provider(profile: AgentProfile) -> BaseLLMProvider:
        """
        Creates and returns an LLM provider instance based on the profile.

        :param profile: The agent profile containing provider type and settings.
        :return: An instance of a class implementing BaseLLMProvider.
        :raises ValueError: If the provider type is not supported.
        """
        if profile.provider == ProviderType.OPENAI:
            return OpenAIProvider()
        
        if profile.provider == ProviderType.OLLAMA:
            return OllamaProvider()
        
        if profile.provider == ProviderType.ANTHROPIC:
            return AnthropicProvider()
        
        # Extend this block as new providers (DeepSeek, XAI, etc.) are implemented
        
        raise ValueError(f"Unsupported provider type: {profile.provider}")