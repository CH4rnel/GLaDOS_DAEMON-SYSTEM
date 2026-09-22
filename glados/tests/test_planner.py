# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock

from glados.core.context import RuntimeContext
from glados.brain.models import TaskInput
from glados.brain.planner import Planner, Plan, PlanStep


class TestPlanner:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.planner = Planner(ctx=self.ctx)

    def test_planner_initialization(self) -> None:
        assert self.planner is not None
        assert self.planner.ctx == self.ctx

    @pytest.mark.asyncio
    async def test_create_plan_returns_plan_object(self) -> None:
        task_input = TaskInput(description="Analyze system logs", priority=2)
        plan = await self.planner.create_plan(task_input)
        
        assert isinstance(plan, Plan)
        assert plan.task_description == "Analyze system logs"
        assert len(plan.steps) > 0

    @pytest.mark.asyncio
    async def test_create_plan_generates_steps(self) -> None:
        task_input = TaskInput(description="Check disk usage", priority=3)
        plan = await self.planner.create_plan(task_input)
        
        assert len(plan.steps) >= 1
        for step in plan.steps:
            assert isinstance(step, PlanStep)
            assert step.step_number > 0
            assert step.action is not None

    @pytest.mark.asyncio
    async def test_create_plan_handles_empty_task(self) -> None:
        task_input = TaskInput(description="   ", priority=1)
        
        with pytest.raises(ValueError, match="empty"):
            await self.planner.create_plan(task_input)

    @pytest.mark.asyncio
    async def test_plan_steps_are_sequential(self) -> None:
        task_input = TaskInput(description="Complex multi-step task", priority=2)
        plan = await self.planner.create_plan(task_input)
        
        step_numbers = [step.step_number for step in plan.steps]
        assert step_numbers == sorted(step_numbers)
        assert step_numbers[0] == 1