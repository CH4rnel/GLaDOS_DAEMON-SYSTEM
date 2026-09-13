# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS LLM Router.
Follows TDD methodology to define the contract for task routing strategies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from glados.llm.router import LLMRouter, RoutingStrategy
from glados.llm.registry import LLMRegistry
from glados.llm.models import (
    AgentProfile,
    LLMMessage,
    LLMResponse,
    ProviderType,
)
from glados.llm.base import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    """Mock provider for testing."""
    
    def __init__(self, response_content: str = "Mock response"):
        self.response_content = response_content
    
    async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
        return LLMResponse(
            content=self.response_content,
            model=profile.model,
            provider=profile.provider,
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
    
    async def health_check(self, profile: AgentProfile) -> bool:
        return True


class TestLLMRouter:
    """Tests for the LLMRouter implementation."""

    def test_router_initialization(self):
        """Test that LLMRouter can be initialized."""
        registry = LLMRegistry()
        router = LLMRouter(registry)
        assert router is not None

    @pytest.mark.asyncio
    async def test_route_single_strategy(self):
        """Test routing with Single strategy."""
        registry = LLMRegistry()
        
        profile = AgentProfile(
            agent_id="test_agent",
            display_name="Test Agent",
            provider=ProviderType.OLLAMA,
            model="test-model",
            tags=["coding"]
        )
        registry.register(profile)
        
        router = LLMRouter(registry)
        router.register_provider(ProviderType.OLLAMA, MockProvider("Single response"))
        
        messages = [LLMMessage(role="user", content="Test")]
        
        result = await router.route(
            messages=messages,
            strategy=RoutingStrategy.SINGLE,
            agent_id="test_agent"
        )
        
        assert isinstance(result, LLMResponse)
        assert result.content == "Single response"

    @pytest.mark.asyncio
    async def test_route_by_tag(self):
        """Test routing to agents by tag."""
        registry = LLMRegistry()
        
        profile1 = AgentProfile(
            agent_id="coder1",
            display_name="Coder 1",
            provider=ProviderType.OLLAMA,
            model="model1",
            tags=["coding"]
        )
        profile2 = AgentProfile(
            agent_id="coder2",
            display_name="Coder 2",
            provider=ProviderType.OPENAI,
            model="gpt-4",
            tags=["coding"]
        )
        
        registry.register(profile1)
        registry.register(profile2)
        
        router = LLMRouter(registry)
        router.register_provider(ProviderType.OLLAMA, MockProvider("Ollama response"))
        router.register_provider(ProviderType.OPENAI, MockProvider("OpenAI response"))
        
        messages = [LLMMessage(role="user", content="Test")]
        
        results = await router.route_by_tag(
            messages=messages,
            tag="coding",
            strategy=RoutingStrategy.PARALLEL
        )
        
        assert len(results) == 2
        assert any(r.content == "Ollama response" for r in results)
        assert any(r.content == "OpenAI response" for r in results)

    @pytest.mark.asyncio
    async def test_route_parallel_strategy(self):
        """Test routing with Parallel strategy."""
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
            model="gpt-4"
        )
        
        registry.register(profile1)
        registry.register(profile2)
        
        router = LLMRouter(registry)
        router.register_provider(ProviderType.OLLAMA, MockProvider("Response 1"))
        router.register_provider(ProviderType.OPENAI, MockProvider("Response 2"))
        
        messages = [LLMMessage(role="user", content="Test")]
        
        results = await router.route(
            messages=messages,
            strategy=RoutingStrategy.PARALLEL,
            agent_ids=["agent1", "agent2"]
        )
        
        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_route_no_agents_found(self):
        """Test routing when no agents match criteria."""
        registry = LLMRegistry()
        router = LLMRouter(registry)
        
        messages = [LLMMessage(role="user", content="Test")]
        
        with pytest.raises(ValueError, match="No agents found"):
            await router.route(
                messages=messages,
                strategy=RoutingStrategy.SINGLE,
                tag="nonexistent"
            )

    @pytest.mark.asyncio
    async def test_route_with_system_prompt(self):
        """Test that system prompt from profile is included."""
        registry = LLMRegistry()
        
        profile = AgentProfile(
            agent_id="test_agent",
            display_name="Test Agent",
            provider=ProviderType.OLLAMA,
            model="test-model",
            system_prompt="You are a helpful assistant."
        )
        registry.register(profile)
        
        router = LLMRouter(registry)
        
        # Create a provider that captures the messages
        captured_messages = []
        
        class CapturingProvider(BaseLLMProvider):
            async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
                captured_messages.extend(messages)
                return LLMResponse(
                    content="Response",
                    model=profile.model,
                    provider=profile.provider
                )
            
            async def health_check(self, profile: AgentProfile) -> bool:
                return True
        
        router.register_provider(ProviderType.OLLAMA, CapturingProvider())
        
        messages = [LLMMessage(role="user", content="Test")]
        
        await router.route(
            messages=messages,
            strategy=RoutingStrategy.SINGLE,
            agent_id="test_agent"
        )
        
        # Verify system prompt was added
        assert len(captured_messages) == 2
        assert captured_messages[0].role == "system"
        assert "helpful assistant" in captured_messages[0].content

    def test_register_provider(self):
        """Test registering a provider for a provider type."""
        registry = LLMRegistry()
        router = LLMRouter(registry)
        
        provider = MockProvider()
        router.register_provider(ProviderType.OLLAMA, provider)
        
        assert router.get_provider(ProviderType.OLLAMA) == provider

    def test_get_nonexistent_provider_raises_error(self):
        """Test that getting a non-registered provider raises error."""
        registry = LLMRegistry()
        router = LLMRouter(registry)
        
        with pytest.raises(ValueError, match="No provider registered"):
            router.get_provider(ProviderType.OPENAI)