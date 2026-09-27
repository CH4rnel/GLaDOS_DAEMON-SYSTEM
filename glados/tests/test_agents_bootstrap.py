# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the agents.yaml bootstrap loader.
Ensures that agent profiles are correctly loaded from configuration,
API keys are resolved from environment variables, and providers are
registered in LLMRegistry via LLMProviderFactory.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from pydantic import SecretStr

from glados.core.bootstrap import AgentsBootstrap
from glados.llm.models import AgentProfile, ProviderType
from glados.llm.registry import LLMRegistry
from glados.llm.providers.openai import OpenAIProvider
from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.anthropic import AnthropicProvider


class TestAgentsBootstrap:
    """Tests for the AgentsBootstrap loader."""

    @pytest.fixture
    def sample_yaml_content(self) -> str:
        return """
agents:
  - agent_id: claude-main
    display_name: Claude Main
    provider: anthropic
    model: claude-sonnet-4-6
    tags: [general, coding]
    api_key_env: ANTHROPIC_API_KEY
  - agent_id: local-qwen
    display_name: Local Qwen
    provider: ollama
    model: qwen2.5:14b
    base_url: http://localhost:11434
    tags: [local, private]
  - agent_id: openai-fast
    display_name: OpenAI Fast
    provider: openai
    model: gpt-4o-mini
    tags: [fast]
    api_key_env: OPENAI_API_KEY
"""

    @pytest.fixture
    def yaml_file(self, tmp_path: Path, sample_yaml_content: str) -> Path:
        config_file = tmp_path / "agents.yaml"
        config_file.write_text(sample_yaml_content)
        return config_file

    def test_load_profiles_from_yaml(self, yaml_file: Path):
        """Test that bootstrap correctly parses YAML into AgentProfile objects."""
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OPENAI_API_KEY": "sk-test-openai",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            profiles = AgentsBootstrap.load_profiles(yaml_file)

        assert len(profiles) == 3
        
        claude_profile = next(p for p in profiles if p.agent_id == "claude-main")
        assert claude_profile.provider == ProviderType.ANTHROPIC
        assert claude_profile.model == "claude-sonnet-4-6"
        assert claude_profile.api_key.get_secret_value() == "sk-ant-test"
        assert "general" in claude_profile.tags

        ollama_profile = next(p for p in profiles if p.agent_id == "local-qwen")
        assert ollama_profile.provider == ProviderType.OLLAMA
        assert ollama_profile.base_url == "http://localhost:11434"
        assert ollama_profile.api_key is None

    def test_load_profiles_raises_on_missing_env_var(self, yaml_file: Path):
        """Test that bootstrap raises error when required API key env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                AgentsBootstrap.load_profiles(yaml_file)
            
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_register_profiles_creates_providers(self, yaml_file: Path):
        """Test that register_profiles creates providers and populates LLMRegistry."""
        mock_registry = MagicMock(spec=LLMRegistry)
        
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OPENAI_API_KEY": "sk-test-openai",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            AgentsBootstrap.register_profiles(yaml_file, mock_registry)

        assert mock_registry.register.call_count == 3
        
        registered_profiles = [
            call.args[0] for call in mock_registry.register.call_args_list
        ]
        registered_providers = [
            call.args[1] for call in mock_registry.register.call_args_list
        ]

        assert any(p.agent_id == "claude-main" for p in registered_profiles)
        assert any(isinstance(provider, AnthropicProvider) for provider in registered_providers)
        assert any(isinstance(provider, OllamaProvider) for provider in registered_providers)
        assert any(isinstance(provider, OpenAIProvider) for provider in registered_providers)

    def test_register_profiles_skips_agents_without_api_key_when_optional(self, tmp_path: Path):
        """Test that agents with missing optional API keys are still registered."""
        config_content = """
agents:
  - agent_id: local-only
    display_name: Local Only
    provider: ollama
    model: llama3.2:latest
    base_url: http://localhost:11434
"""
        config_file = tmp_path / "agents.yaml"
        config_file.write_text(config_content)
        
        mock_registry = MagicMock(spec=LLMRegistry)
        
        with patch.dict(os.environ, {}, clear=True):
            AgentsBootstrap.register_profiles(config_file, mock_registry)

        assert mock_registry.register.call_count == 1