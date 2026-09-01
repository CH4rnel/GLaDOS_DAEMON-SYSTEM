# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Base classes and models for the GLaDOS Tool subsystem.
Defines the core contract that all low-level tools must implement.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext


class ToolDefinition(BaseModel):
    """
    Metadata and schema definition for a tool.
    Used by the Brain/Planner to understand what a tool does and how to call it.
    """
    name: str = Field(..., min_length=1, description="Unique identifier for the tool")
    description: str = Field(..., min_length=1, description="Human-readable description of the tool's purpose")
    parameters: dict[str, Any] = Field(
        default_factory=dict, 
        description="JSON schema defining the expected parameters for execution"
    )


class BaseTool(ABC):
    """
    Abstract base class for all GLaDOS tools.
    Tools are low-level, deterministic executors (e.g., shell, fs, git).
    """

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Returns the metadata definition of this tool."""
        pass

    @abstractmethod
    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the tool's logic.
        
        :param ctx: The global runtime context (provides access to memory, logger, etc.).
        :param params: Validated parameters for this specific execution.
        :return: The result of the execution (usually a string or dict).
        """
        pass