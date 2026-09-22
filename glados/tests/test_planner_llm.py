# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
import json
from unittest.mock import MagicMock, AsyncMock

from glados.core.context import RuntimeContext
from glados.brain.models import TaskInput
from glados.brain.planner import Planner


class TestPlannerLLMIntegration:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.ctx.llm_router = MagicMock()
        self.planner = Planner(ctx=self.ctx)

    @pytest.mark.asyncio
    async def test_create_plan_calls_llm_router(self) -> None:
        llm_response = json.dumps({
            "steps": [
                {"action": "Check disk", "tool_name": "disk_usage", "parameters": {}}
            ]
        })
        self.ctx.llm_router.generate = AsyncMock(return_value=llm_response)
        
        task_input = TaskInput(description="Check disk space", priority=2)
        context = [{"role": "user", "content": "previous task"}]
        plan = await self.planner.create_plan(task_input, context)
        
        self.ctx.llm_router.generate.assert_called_once()
        assert len(plan.steps) == 1
        assert plan.steps[0].tool_name == "disk_usage"

    @pytest.mark.asyncio
    async def test_create_plan_parses_multi_step_response(self) -> None:
        llm_response = json.dumps({
            "steps": [
                {"action": "Get CPU info", "tool_name": "system_info", "parameters": {"type": "cpu"}},
                {"action": "Log result", "tool_name": "write_file", "parameters": {"path": "/tmp/cpu.txt"}}
            ]
        })
        self.ctx.llm_router.generate = AsyncMock(return_value=llm_response)
        
        task_input = TaskInput(description="Analyze CPU", priority=3)
        plan = await self.planner.create_plan(task_input, [])
        
        assert len(plan.steps) == 2
        assert plan.steps[0].step_number == 1
        assert plan.steps[1].step_number == 2
        assert plan.steps[0].tool_name == "system_info"
        assert plan.steps[1].tool_name == "write_file"

    @pytest.mark.asyncio
    async def test_create_plan_falls_back_on_llm_failure(self) -> None:
        self.ctx.llm_router.generate = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        
        task_input = TaskInput(description="Check system", priority=2)
        plan = await self.planner.create_plan(task_input, [])
        
        # Fallback should still produce a valid plan
        assert len(plan.steps) >= 1
        assert plan.task_description == "Check system"

    @pytest.mark.asyncio
    async def test_create_plan_falls_back_on_invalid_json(self) -> None:
        self.ctx.llm_router.generate = AsyncMock(return_value="not a valid json {{{")
        
        task_input = TaskInput(description="Analyze logs", priority=2)
        plan = await self.planner.create_plan(task_input, [])
        
        # Fallback should still produce a valid plan
        assert len(plan.steps) >= 1
        assert plan.task_description == "Analyze logs"

    @pytest.mark.asyncio
    async def test_create_plan_falls_back_on_missing_steps_key(self) -> None:
        self.ctx.llm_router.generate = AsyncMock(return_value=json.dumps({"no_steps_here": []}))
        
        task_input = TaskInput(description="Do something", priority=2)
        plan = await self.planner.create_plan(task_input, [])
        
        # Fallback should still produce a valid plan
        assert len(plan.steps) >= 1