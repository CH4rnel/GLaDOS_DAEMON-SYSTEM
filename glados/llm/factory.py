# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Factory for creating LLM provider instances based on AgentProfile.
"""

from glados.llm.models import AgentProfile, ProviderType
from glados.llm.providers.anthropic import AnthropicProvider
from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.openai import OpenAIProvider
from glados.llm.providers.deepseek import DeepSeekProvider
from glados.llm.providers.groq import GroqProvider
from glados.llm.providers.qwen import QwenProvider


class LLMProviderFactory:
    """Creates LLM provider instances based on the agent's profile configuration."""

    @staticmethod
    def create_provider(profile: AgentProfile):
        """
        Instantiates the correct LLM provider for the given profile.
        All providers are designed to accept a single `profile` argument.
        """
        if profile.provider == ProviderType.ANTHROPIC:
            return AnthropicProvider(profile)
        if profile.provider == ProviderType.OLLAMA:
            return OllamaProvider(profile)
        if profile.provider == ProviderType.OPENAI:
            return OpenAIProvider(profile)
        if profile.provider == ProviderType.DEEPSEEK:
            return DeepSeekProvider(profile)
        if profile.provider == ProviderType.GROQ:
            return GroqProvider(profile)
        if profile.provider == ProviderType.QWEN:
            return QwenProvider(profile)
        
        raise ValueError(f"Unsupported provider type: {profile.provider}")