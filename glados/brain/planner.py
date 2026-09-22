# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from loguru import logger

from glados.brain.models import TaskInput

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


@dataclass
class PlanStep:
    """Represents a single step in an execution plan."""
    step_number: int
    action: str
    tool_name: str | None = None
    parameters: dict = field(default_factory=dict)


@dataclass
class Plan:
    """Represents a structured execution plan for a task."""
    task_description: str
    steps: List[PlanStep] = field(default_factory=list)
    
    def add_step(self, action: str, tool_name: str | None = None, parameters: dict | None = None) -> None:
        """Adds a new step to the plan."""
        step_number = len(self.steps) + 1
        step = PlanStep(
            step_number=step_number,
            action=action,
            tool_name=tool_name,
            parameters=parameters or {}
        )
        self.steps.append(step)


class Planner:
    """
    Generates structured execution plans from task descriptions.
    Currently uses rule-based planning; will integrate with LLM for intelligent planning.
    """

    def __init__(self, ctx: "RuntimeContext") -> None:
        self.ctx = ctx
        self.logger = logger.bind(component="Planner")
        self.logger.info("Planner initialized")

    async def create_plan(self, task_input: TaskInput) -> Plan:
        """
        Creates an execution plan for the given task.
        
        :param task_input: Task description and metadata
        :return: Structured execution plan
        :raises ValueError: If task description is empty
        """
        if not task_input.description or not task_input.description.strip():
            raise ValueError("Task description cannot be empty")
        
        self.logger.info(f"Creating plan for task: {task_input.description}")
        
        plan = Plan(task_description=task_input.description)
        
        # TODO: Integrate with LLM for intelligent planning
        # For now, generate a basic single-step plan
        plan.add_step(
            action=f"Process task: {task_input.description}",
            tool_name=None,
            parameters={"priority": task_input.priority}
        )
        
        self.logger.debug(f"Generated plan with {len(plan.steps)} step(s)")
        
        return plan