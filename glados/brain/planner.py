# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Planner subsystem for GLaDOS_DAEMON-SYSTEM.
Responsible for breaking down high-level tasks into executable steps.
"""

from typing import Literal
from pydantic import BaseModel, Field

from glados.brain.engine import TaskInput


class PlanStep(BaseModel):
    """Represents a single actionable step within a plan."""
    step_id: int = Field(..., ge=1, description="Unique identifier for the step")
    action: str = Field(..., min_length=1, description="The action to be performed")
    description: str = Field(..., min_length=1, description="Detailed description of the step")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending", description="Current execution status"
    )


class Plan(BaseModel):
    """Represents a complete execution plan for a task."""
    task_description: str = Field(..., description="Original task description")
    steps: list[PlanStep] = Field(default_factory=list, description="Ordered list of steps")


class Planner:
    """
    Core planning engine.
    Currently uses a deterministic mock logic. 
    Will be replaced by LLM-based planning in Phase 6.
    """

    def __init__(self) -> None:
        """Initializes the Planner."""
        pass

    def create_plan(self, task: TaskInput) -> Plan:
        """
        Generates an execution plan for a given task.
        
        :param task: The validated input task.
        :return: A structured Plan object.
        """
        # TODO (Phase 6): Replace this mock logic with LLM inference
        steps = self._generate_mock_steps(task)
        
        return Plan(
            task_description=task.description,
            steps=steps
        )

    def _generate_mock_steps(self, task: TaskInput) -> list[PlanStep]:
        """
        Generates deterministic mock steps for testing and bootstrapping.
        
        :param task: The input task.
        :return: List of mock PlanSteps.
        """
        return [
            PlanStep(
                step_id=1, 
                action="analyze", 
                description=f"Analyze requirements for: {task.description}"
            ),
            PlanStep(
                step_id=2, 
                action="execute", 
                description=f"Execute core logic for: {task.description}"
            ),
            PlanStep(
                step_id=3, 
                action="verify", 
                description="Verify execution results and report status"
            )
        ]