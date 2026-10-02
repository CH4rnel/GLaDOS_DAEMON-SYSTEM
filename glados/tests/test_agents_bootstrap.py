# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the agents.yaml bootstrap loader.
Ensures that agent profiles are correctly loaded from configuration,
API keys are resolved from environment variables (${VAR} syntax), and 
providers are registered in LLMRegistry via LLMProviderFactory.
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
        return r"""
agents:
  - agent_id: claude_writing
    display_name: Claude Writing Assistant
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: ${ANTHROPIC_API_KEY}
    tags: [writing, documentation]
  - agent_id: local_qwen_coder
    display_name: Local Qwen Coder
    provider: ollama
    model: qwen2.5-coder:7b
    base_url: ${OLLAMA_BASE_URL}
    tags: [coding, python, fast]
  - agent_id: gpt4_analyst
    display_name: GPT-4 Analyst
    provider: openai
    model: gpt-4-turbo
    api_key: ${OPENAI_API_KEY}
    tags: [analysis, security]
"""

    @pytest.fixture
    def yaml_file(self, tmp_path: Path, sample_yaml_content: str) -> Path:
        config_file = tmp_path / "agents.yaml"
        config_file.write_text(sample_yaml_content)
        return config_file

    def test_load_profiles_from_yaml(self, yaml_file: Path):
        """Test that bootstrap correctly parses YAML and resolves ${VAR} syntax."""
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OPENAI_API_KEY": "sk-test-openai",
            "OLLAMA_BASE_URL": "http://localhost:11434",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            profiles = AgentsBootstrap.load_profiles(yaml_file)

        assert len(profiles) == 3
        
        claude_profile = next(p for p in profiles if p.agent_id == "claude_writing")
        assert claude_profile.provider == ProviderType.ANTHROPIC
        assert claude_profile.api_key.get_secret_value() == "sk-ant-test"
        assert "writing" in claude_profile.tags

        ollama_profile = next(p for p in profiles if p.agent_id == "local_qwen_coder")
        assert ollama_profile.provider == ProviderType.OLLAMA
        assert ollama_profile.base_url == "http://localhost:11434"

    def test_load_profiles_skips_agents_without_api_key(self, yaml_file: Path):
        """Test that bootstrap gracefully skips agents when required API key env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            profiles = AgentsBootstrap.load_profiles(yaml_file)
        
        assert len(profiles) == 1
        assert profiles[0].agent_id == "local_qwen_coder"
        assert profiles[0].base_url is None

    def test_register_profiles_creates_providers(self, yaml_file: Path):
        """Test that register_profiles creates providers and populates LLMRegistry."""
        mock_registry = MagicMock(spec=LLMRegistry)
        
        env_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "OPENAI_API_KEY": "sk-test-openai",
            "OLLAMA_BASE_URL": "http://localhost:11434",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            AgentsBootstrap.register_profiles(yaml_file, mock_registry)

        assert mock_registry.register.call_count == 3
        
        registered_profiles = [call.args[0] for call in mock_registry.register.call_args_list]
        registered_providers = [call.args[1] for call in mock_registry.register.call_args_list]

        assert any(p.agent_id == "claude_writing" for p in registered_profiles)
        assert any(isinstance(provider, AnthropicProvider) for provider in registered_providers)
        assert any(isinstance(provider, OllamaProvider) for provider in registered_providers)
        assert any(isinstance(provider, OpenAIProvider) for provider in registered_providers)