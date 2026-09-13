# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for BrainEngine integration with LLMRouter.
Follows TDD methodology to define the contract for LLM-powered planning.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from glados.brain.engine import BrainEngine
from glados.brain.models import TaskInput, ExecutionResult
from glados.core.context import RuntimeContext
from glados.core.identity import Identity
from glados.llm.registry import LLMRegistry
from glados.llm.router import LLMRouter, RoutingStrategy
from glados.llm.models import (
    AgentProfile,
    LLMMessage,
    LLMResponse,
    ProviderType,
)
from glados.llm.base import BaseLLMProvider
from glados.memory.manager import MemoryManager
from glados.skills.registry import SkillRegistry
from glados.tools.registry import ToolRegistry
from loguru import logger
from pathlib import Path


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response_content: str = "Mock LLM response"):
        self.response_content = response_content
        self.call_count = 0
    
    async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            content=self.response_content,
            model=profile.model,
            provider=profile.provider,
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
    
    async def health_check(self, profile: AgentProfile) -> bool:
        return True


class TestBrainEngineLLMIntegration:
    """Tests for BrainEngine integration with LLMRouter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.identity = Identity(
            name="GLaDOS",
            codename="Test",
            version="0.1.0",
            owner={"username": "test", "environment": "test"},
            system={"os": "Linux", "arch": "x86_64"},  # fix: added system field
            purpose="Testing",
            personality={},
            principles=[]
        )
        
        self.memory = MemoryManager(
            stm_max_size=10,
            ltm_path=Path("test_memory.json")
        )
        
        self.skills = SkillRegistry()
        self.tools = ToolRegistry()
        
        self.llm_registry = LLMRegistry()
        self.llm_router = LLMRouter(self.llm_registry)
        
        self.ctx = RuntimeContext(
            identity=self.identity,
            logger=logger,
            memory=self.memory,
            skills=self.skills,
            tools=self.tools,
            llm_agents=self.llm_registry,
            llm_router=self.llm_router,
        )

    def test_brain_engine_with_llm_router(self):
        """Test that BrainEngine can be initialized with LLMRouter."""
        engine = BrainEngine(self.ctx)
        assert engine is not None
        assert engine._ctx.llm_router is not None

    @pytest.mark.asyncio
    async def test_process_task_with_llm_planning(self):
        """Test that process_task uses LLMRouter for planning."""
        # Register a test agent
        profile = AgentProfile(
            agent_id="test_planner",
            display_name="Test Planner",
            provider=ProviderType.OLLAMA,
            model="test-model",
            tags=["planning"]
        )
        self.llm_registry.register(profile)
        
        # Register mock provider
        mock_provider = MockLLMProvider("Generated plan: Step 1, Step 2, Step 3")
        self.llm_router.register_provider(ProviderType.OLLAMA, mock_provider)
        
        engine = BrainEngine(self.ctx)
        
        task = TaskInput(
            description="Test task for LLM planning",
            priority=3
        )
        
        result = await engine.process_task(task)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        # Verify that LLM was called
        assert mock_provider.call_count > 0

    @pytest.mark.asyncio
    async def test_process_task_without_llm_router_falls_back_to_mock(self):
        """Test that process_task falls back to mock planner if no LLM available."""
        # Don't register any agents
        engine = BrainEngine(self.ctx)
        
        task = TaskInput(
            description="Test task without LLM",
            priority=2
        )
        
        result = await engine.process_task(task)
        
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        # Should still work with mock planner
        assert "plan" in result.message.lower() or result.data.get("plan_steps_count", 0) > 0

    @pytest.mark.asyncio
    async def test_process_task_with_specific_agent(self):
        """Test that process_task can route to a specific agent."""
        profile = AgentProfile(
            agent_id="specific_agent",
            display_name="Specific Agent",
            provider=ProviderType.OPENAI,
            model="gpt-4",
            tags=["planning"]
        )
        self.llm_registry.register(profile)
        
        mock_provider = MockLLMProvider("Specific agent response")
        self.llm_router.register_provider(ProviderType.OPENAI, mock_provider)
        
        engine = BrainEngine(self.ctx)
        
        task = TaskInput(
            description="Task for specific agent",
            priority=4,
            metadata={"preferred_agent": "specific_agent"}
        )
        
        result = await engine.process_task(task)
        
        assert result.success is True
        assert mock_provider.call_count > 0

    @pytest.mark.asyncio
    async def test_process_task_with_tag_routing(self):
        """Test that process_task can route by tag."""
        profile1 = AgentProfile(
            agent_id="coder1",
            display_name="Coder 1",
            provider=ProviderType.OLLAMA,
            model="qwen",
            tags=["coding", "planning"]
        )
        profile2 = AgentProfile(
            agent_id="coder2",
            display_name="Coder 2",
            provider=ProviderType.OPENAI,
            model="gpt-4",
            tags=["coding", "planning"]
        )
        
        self.llm_registry.register(profile1)
        self.llm_registry.register(profile2)
        
        mock_provider = MockLLMProvider("Coding response")
        self.llm_router.register_provider(ProviderType.OLLAMA, mock_provider)
        self.llm_router.register_provider(ProviderType.OPENAI, mock_provider)
        
        engine = BrainEngine(self.ctx)
        
        task = TaskInput(
            description="Coding task",
            priority=5,
            metadata={"preferred_tag": "coding"}
        )
        
        result = await engine.process_task(task)
        
        assert result.success is True