# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock

from glados.core.context import RuntimeContext
from glados.brain.models import TaskInput
from glados.brain.engine import BrainEngine


class TestBrainEngine:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.ctx.memory = MagicMock()
        self.ctx.llm_router = MagicMock()
        self.ctx.tools = MagicMock()
        self.engine = BrainEngine(ctx=self.ctx)

    def test_brain_engine_initialization(self) -> None:
        assert self.engine is not None
        assert self.engine.ctx == self.ctx

    @pytest.mark.asyncio
    async def test_process_task_returns_result(self) -> None:
        task_input = TaskInput(description="Test task", priority=3)
        result = await self.engine.process_task(task_input)
        
        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_process_task_logs_task_description(self) -> None:
        task_input = TaskInput(description="Analyze system logs", priority=2)
        result = await self.engine.process_task(task_input)
        
        assert result.success is True
        assert "Analyze system logs" in result.message

    @pytest.mark.asyncio
    async def test_process_task_handles_whitespace_only_description(self) -> None:
        task_input = TaskInput(description="   ", priority=1)
        result = await self.engine.process_task(task_input)
        
        assert result.success is False
        assert "empty" in result.message.lower()

    @pytest.mark.asyncio
    async def test_process_task_retrieves_memory_context(self) -> None:
        self.ctx.memory.get_short_term_context.return_value = [{"role": "user", "content": "previous task"}]
        task_input = TaskInput(description="Continue previous work", priority=2)
        
        result = await self.engine.process_task(task_input)
        
        self.ctx.memory.get_short_term_context.assert_called_once()
        assert result.success is True
        assert "context" in result.data