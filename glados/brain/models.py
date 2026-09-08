# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Data models and schemas for the GLaDOS Brain subsystem.
"""

from typing import Any

from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    """Input task model for validation and structuring."""
    description: str = Field(..., min_length=1, description="Task description from user or system")
    priority: int = Field(default=1, ge=1, le=5, description="Task priority (1-5)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExecutionResult(BaseModel):
    """Task execution result model."""
    success: bool = Field(..., description="Success flag")
    message: str = Field(..., min_length=1, description="Human-readable result message")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured result data")


class PlanStep(BaseModel):
    """Represents a single actionable step within a plan."""
    step_id: int = Field(..., ge=1, description="Unique identifier for the step")
    action: str = Field(..., min_length=1, description="The action to be performed")
    description: str = Field(..., min_length=1, description="Detailed description of the step")
    status: str = Field(
        default="pending", 
        description="Current execution status",
        pattern="^(pending|in_progress|completed|failed)$"
    )


class Plan(BaseModel):
    """Represents a complete execution plan for a task."""
    task_description: str = Field(..., min_length=1, description="Original task description")
    steps: list[PlanStep] = Field(default_factory=list, description="Ordered list of steps")