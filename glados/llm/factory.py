# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""Factory for creating LLM provider instances based on AgentProfile."""

from glados.llm.models import AgentProfile, ProviderType
from glados.llm.providers.anthropic import AnthropicProvider
from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.openai import OpenAIProvider
from glados.llm.providers.deepseek import DeepSeekProvider
from glados.llm.providers.groq import GroqProvider
from glados.llm.providers.qwen import QwenProvider
from glados.llm.providers.gemini import GeminiProvider
from glados.llm.providers.mistral import MistralProvider

class LLMProviderFactory:
    @staticmethod
    def create_provider(profile: AgentProfile):
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
        if profile.provider == ProviderType.GOOGLE:
            return GeminiProvider(profile)
        if profile.provider == ProviderType.MISTRAL:
            return MistralProvider(profile)
        
        raise ValueError(f"Unsupported provider type: {profile.provider}")