# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

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
    message: str = Field(..., description="Human-readable result message")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured result data")