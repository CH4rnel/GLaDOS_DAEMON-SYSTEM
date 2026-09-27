# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS LLM Provider Factory.
Ensures correct instantiation of providers based on AgentProfile configuration.
"""

import pytest
from pydantic import SecretStr

from glados.llm.factory import LLMProviderFactory
from glados.llm.models import AgentProfile, ProviderType
from glados.llm.providers.openai import OpenAIProvider
from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.anthropic import AnthropicProvider


class TestLLMProviderFactory:
    """Tests for the LLMProviderFactory implementation."""

    def test_create_openai_provider(self):
        """Test factory creates OpenAIProvider for OPENAI type."""
        profile = AgentProfile(
            agent_id="test_openai",
            display_name="Test OpenAI",
            provider=ProviderType.OPENAI,
            model="gpt-4o",
            api_key=SecretStr("sk-test")
        )
        provider = LLMProviderFactory.create_provider(profile)
        assert isinstance(provider, OpenAIProvider)

    def test_create_ollama_provider(self):
        """Test factory creates OllamaProvider for OLLAMA type."""
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="llama3.2:latest",
            base_url="http://localhost:11434"
        )
        provider = LLMProviderFactory.create_provider(profile)
        assert isinstance(provider, OllamaProvider)

    def test_create_anthropic_provider(self):
        """Test factory creates AnthropicProvider for ANTHROPIC type."""
        profile = AgentProfile(
            agent_id="test_anthropic",
            display_name="Test Anthropic",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=SecretStr("sk-ant-test")
        )
        provider = LLMProviderFactory.create_provider(profile)
        assert isinstance(provider, AnthropicProvider)

    def test_create_unsupported_provider_raises_error(self):
        """Test factory raises ValueError for unsupported provider types."""
        profile = AgentProfile(
            agent_id="test_unknown",
            display_name="Test Unknown",
            provider=ProviderType.CUSTOM,
            model="unknown-model"
        )
        with pytest.raises(ValueError) as exc_info:
            LLMProviderFactory.create_provider(profile)
        
        assert "Unsupported provider type" in str(exc_info.value)