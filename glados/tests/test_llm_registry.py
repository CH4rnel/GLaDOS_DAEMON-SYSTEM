# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS LLM Registry.
Follows TDD methodology to define the contract for agent profile management.
"""

import pytest

# These imports will fail initially (Red Phase)
from glados.llm.registry import LLMRegistry, AgentNotFoundError
from glados.llm.models import AgentProfile, ProviderType


class TestLLMRegistry:
    """Tests for the LLMRegistry implementation."""

    def test_registry_initialization(self):
        """Test that LLMRegistry can be initialized."""
        registry = LLMRegistry()
        assert registry is not None

    def test_register_agent_profile(self):
        """Test registering an agent profile."""
        registry = LLMRegistry()
        profile = AgentProfile(
            agent_id="test_agent",
            display_name="Test Agent",
            provider=ProviderType.OLLAMA,
            model="test-model"
        )
        
        registry.register(profile)
        
        assert len(registry.list_all()) == 1
        assert registry.get("test_agent") == profile

    def test_register_duplicate_agent_raises_error(self):
        """Test that registering a duplicate agent_id raises ValueError."""
        registry = LLMRegistry()
        profile1 = AgentProfile(
            agent_id="duplicate",
            display_name="First",
            provider=ProviderType.OLLAMA,
            model="model1"
        )
        profile2 = AgentProfile(
            agent_id="duplicate",
            display_name="Second",
            provider=ProviderType.OPENAI,
            model="model2"
        )
        
        registry.register(profile1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(profile2)

    def test_unregister_agent(self):
        """Test unregistering an agent profile."""
        registry = LLMRegistry()
        profile = AgentProfile(
            agent_id="to_remove",
            display_name="Remove Me",
            provider=ProviderType.OLLAMA,
            model="test"
        )
        
        registry.register(profile)
        assert len(registry.list_all()) == 1
        
        registry.unregister("to_remove")
        assert len(registry.list_all()) == 0

    def test_unregister_nonexistent_agent_raises_error(self):
        """Test that unregistering a non-existent agent raises AgentNotFoundError."""
        registry = LLMRegistry()
        
        with pytest.raises(AgentNotFoundError):
            registry.unregister("nonexistent")

    def test_get_agent_by_id(self):
        """Test retrieving an agent by ID."""
        registry = LLMRegistry()
        profile = AgentProfile(
            agent_id="find_me",
            display_name="Find Me",
            provider=ProviderType.OPENAI,
            model="gpt-4"
        )
        
        registry.register(profile)
        retrieved = registry.get("find_me")
        
        assert retrieved == profile
        assert retrieved.agent_id == "find_me"

    def test_get_nonexistent_agent_raises_error(self):
        """Test that getting a non-existent agent raises AgentNotFoundError."""
        registry = LLMRegistry()
        
        with pytest.raises(AgentNotFoundError):
            registry.get("nonexistent")

    def test_get_by_tag(self):
        """Test retrieving agents by tag."""
        registry = LLMRegistry()
        
        profile1 = AgentProfile(
            agent_id="coder1",
            display_name="Coder 1",
            provider=ProviderType.OLLAMA,
            model="qwen",
            tags=["coding", "python"]
        )
        profile2 = AgentProfile(
            agent_id="coder2",
            display_name="Coder 2",
            provider=ProviderType.OPENAI,
            model="gpt-4",
            tags=["coding", "javascript"]
        )
        profile3 = AgentProfile(
            agent_id="analyst",
            display_name="Analyst",
            provider=ProviderType.ANTHROPIC,
            model="claude",
            tags=["analysis"]
        )
        
        registry.register(profile1)
        registry.register(profile2)
        registry.register(profile3)
        
        coders = registry.get_by_tag("coding")
        assert len(coders) == 2
        assert profile1 in coders
        assert profile2 in coders
        
        python_coders = registry.get_by_tag("python")
        assert len(python_coders) == 1
        assert profile1 in python_coders

    def test_get_by_tag_no_matches(self):
        """Test that get_by_tag returns empty list when no agents match."""
        registry = LLMRegistry()
        profile = AgentProfile(
            agent_id="test",
            display_name="Test",
            provider=ProviderType.OLLAMA,
            model="test",
            tags=["coding"]
        )
        
        registry.register(profile)
        
        result = registry.get_by_tag("nonexistent_tag")
        assert result == []

    def test_get_by_provider(self):
        """Test retrieving agents by provider type."""
        registry = LLMRegistry()
        
        profile1 = AgentProfile(
            agent_id="ollama1",
            display_name="Ollama 1",
            provider=ProviderType.OLLAMA,
            model="model1"
        )
        profile2 = AgentProfile(
            agent_id="ollama2",
            display_name="Ollama 2",
            provider=ProviderType.OLLAMA,
            model="model2"
        )
        profile3 = AgentProfile(
            agent_id="openai1",
            display_name="OpenAI 1",
            provider=ProviderType.OPENAI,
            model="gpt-4"
        )
        
        registry.register(profile1)
        registry.register(profile2)
        registry.register(profile3)
        
        ollama_agents = registry.get_by_provider(ProviderType.OLLAMA)
        assert len(ollama_agents) == 2
        assert profile1 in ollama_agents
        assert profile2 in ollama_agents
        
        openai_agents = registry.get_by_provider(ProviderType.OPENAI)
        assert len(openai_agents) == 1
        assert profile3 in openai_agents

    def test_list_all_agents(self):
        """Test listing all registered agents."""
        registry = LLMRegistry()
        
        profile1 = AgentProfile(
            agent_id="agent1",
            display_name="Agent 1",
            provider=ProviderType.OLLAMA,
            model="model1"
        )
        profile2 = AgentProfile(
            agent_id="agent2",
            display_name="Agent 2",
            provider=ProviderType.OPENAI,
            model="model2"
        )
        
        registry.register(profile1)
        registry.register(profile2)
        
        all_agents = registry.list_all()
        assert len(all_agents) == 2
        assert profile1 in all_agents
        assert profile2 in all_agents

    def test_get_active_agents(self):
        """Test retrieving only active agents."""
        registry = LLMRegistry()
        
        profile1 = AgentProfile(
            agent_id="active_agent",
            display_name="Active",
            provider=ProviderType.OLLAMA,
            model="model1",
            is_active=True
        )
        profile2 = AgentProfile(
            agent_id="inactive_agent",
            display_name="Inactive",
            provider=ProviderType.OPENAI,
            model="model2",
            is_active=False
        )
        
        registry.register(profile1)
        registry.register(profile2)
        
        active_agents = registry.get_active()
        assert len(active_agents) == 1
        assert profile1 in active_agents
        assert profile2 not in active_agents

    def test_registry_is_empty_initially(self):
        """Test that a new registry is empty."""
        registry = LLMRegistry()
        assert registry.list_all() == []
        assert registry.get_active() == []