# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS ConfigLoader agent profile loading functionality.
Follows TDD methodology to define the contract for loading agent profiles from YAML and .env.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from glados.config.loader import ConfigLoader
from glados.llm.models import AgentProfile, ProviderType


class TestConfigLoaderAgentProfiles:
    """Tests for loading agent profiles from configuration."""

    def test_load_agent_profiles_from_yaml(self, tmp_path: Path):
        """Test loading agent profiles from a YAML file."""
        # Create a temporary agents.yaml
        agents_yaml = tmp_path / "agents.yaml"
        agents_yaml.write_text("""
agents:
  - agent_id: local_qwen
    display_name: Local Qwen Coder
    provider: ollama
    model: qwen2.5-coder:7b
    base_url: http://localhost:11434
    system_prompt: "You are an expert Python developer."
    tags: ["coding", "python"]
    
  - agent_id: gpt4_analyst
    display_name: GPT-4 Analyst
    provider: openai
    model: gpt-4-turbo
    api_key: sk-test-key-123
    system_prompt: "Analyze system logs."
    tags: ["analysis"]
""")
        
        loader = ConfigLoader(config_dir=tmp_path)
        profiles = loader.load_agent_profiles()
        
        assert len(profiles) == 2
        assert profiles[0].agent_id == "local_qwen"
        assert profiles[0].provider == ProviderType.OLLAMA
        assert profiles[1].agent_id == "gpt4_analyst"
        assert profiles[1].provider == ProviderType.OPENAI
        assert profiles[1].api_key == "sk-test-key-123"

    def test_load_agent_profiles_with_env_substitution(self, tmp_path: Path):
        """Test that environment variables are substituted in agent profiles."""
        agents_yaml = tmp_path / "agents.yaml"
        agents_yaml.write_text("""
agents:
  - agent_id: secure_agent
    display_name: Secure Agent
    provider: openai
    model: gpt-4
    api_key: ${TEST_OPENAI_KEY}
    base_url: ${TEST_BASE_URL}
""")
        
        # Mock environment variables
        with patch.dict(os.environ, {
            "TEST_OPENAI_KEY": "sk-secret-from-env",
            "TEST_BASE_URL": "https://custom.api.com/v1"
        }):
            loader = ConfigLoader(config_dir=tmp_path)
            profiles = loader.load_agent_profiles()
            
            assert len(profiles) == 1
            assert profiles[0].api_key == "sk-secret-from-env"
            assert profiles[0].base_url == "https://custom.api.com/v1"

    def test_load_agent_profiles_missing_env_var_raises_error(self, tmp_path: Path):
        """Test that missing environment variables raise a clear error."""
        agents_yaml = tmp_path / "agents.yaml"
        agents_yaml.write_text("""
agents:
  - agent_id: broken_agent
    display_name: Broken Agent
    provider: openai
    model: gpt-4
    api_key: ${NONEXISTENT_KEY}
""")
        
        loader = ConfigLoader(config_dir=tmp_path)
        
        with pytest.raises(ValueError, match="Environment variable 'NONEXISTENT_KEY' not found"):
            loader.load_agent_profiles()

    def test_load_agent_profiles_empty_file(self, tmp_path: Path):
        """Test loading from an empty agents.yaml returns empty list."""
        agents_yaml = tmp_path / "agents.yaml"
        agents_yaml.write_text("agents: []")
        
        loader = ConfigLoader(config_dir=tmp_path)
        profiles = loader.load_agent_profiles()
        
        assert profiles == []

    def test_load_agent_profiles_missing_file(self, tmp_path: Path):
        """Test that missing agents.yaml returns empty list (not an error)."""
        loader = ConfigLoader(config_dir=tmp_path)
        profiles = loader.load_agent_profiles()
        
        assert profiles == []

    def test_load_agent_profiles_invalid_yaml(self, tmp_path: Path):
        """Test that invalid YAML raises an error."""
        agents_yaml = tmp_path / "agents.yaml"
        agents_yaml.write_text("invalid: yaml: content: [")
        
        loader = ConfigLoader(config_dir=tmp_path)
        
        with pytest.raises(Exception):  # yaml.YAMLError or similar
            loader.load_agent_profiles()

    def test_load_agent_profiles_validation_error(self, tmp_path: Path):
        """Test that invalid agent profile data raises ValidationError."""
        agents_yaml = tmp_path / "agents.yaml"
        agents_yaml.write_text("""
agents:
  - agent_id: invalid_agent
    display_name: Invalid
    provider: invalid_provider_type
    model: test
""")
        
        loader = ConfigLoader(config_dir=tmp_path)
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            loader.load_agent_profiles()