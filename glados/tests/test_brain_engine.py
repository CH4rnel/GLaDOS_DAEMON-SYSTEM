# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, AsyncMock

from glados.core.context import RuntimeContext
from glados.brain.models import TaskInput
from glados.brain.engine import BrainEngine


class TestBrainEngine:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.ctx.memory = MagicMock()
        self.ctx.memory.get_short_term_context.return_value = []
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
        self.ctx.memory.get_short_term_context.return_value = [
            {"role": "user", "content": "previous task"}
        ]
        task_input = TaskInput(description="Continue previous work", priority=2)

        result = await self.engine.process_task(task_input)

        self.ctx.memory.get_short_term_context.assert_called_once()
        assert result.success is True
        assert "context_records_count" in result.data

    @pytest.mark.asyncio
    async def test_process_task_executes_plan_steps(self) -> None:
        mock_plan = MagicMock()
        mock_step = MagicMock()
        mock_step.step_number = 1
        mock_step.action = "Get system info"
        mock_step.tool_name = "system_info"
        mock_step.parameters = {"detail": "cpu"}
        mock_plan.steps = [mock_step]

        self.engine.planner.create_plan = AsyncMock(return_value=mock_plan)
        self.ctx.tools.execute = AsyncMock(return_value={"status": "ok"})

        task_input = TaskInput(description="Check CPU", priority=2)
        result = await self.engine.process_task(task_input)

        self.ctx.tools.execute.assert_called_once_with("system_info", {"detail": "cpu"})
        assert result.success is True
        assert "execution_results" in result.data

    @pytest.mark.asyncio
    async def test_process_task_stores_result_in_memory(self) -> None:
        task_input = TaskInput(description="Analyze logs", priority=2)

        result = await self.engine.process_task(task_input)

        assert result.success is True
        self.ctx.memory.add_short_term_record.assert_called_once()
        call_args = self.ctx.memory.add_short_term_record.call_args
        assert call_args[0][0] == "brain"
        assert "Analyze logs" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_process_task_handles_missing_memory_gracefully(self) -> None:
        self.ctx.memory = None
        self.engine = BrainEngine(ctx=self.ctx)

        task_input = TaskInput(description="Work without memory", priority=2)
        result = await self.engine.process_task(task_input)

        assert result.success is True