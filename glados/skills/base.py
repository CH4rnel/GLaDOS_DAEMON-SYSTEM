# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Base classes and models for the GLaDOS Skill subsystem.
Defines the core contract that all skills must implement.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext


class SkillDefinition(BaseModel):
    """
    Metadata and schema definition for a skill.
    Used by the Brain/Planner to understand what a skill does and how to call it.
    """
    name: str = Field(..., min_length=1, description="Unique identifier for the skill")
    description: str = Field(..., min_length=1, description="Human-readable description of the skill's purpose")
    parameters: dict[str, Any] = Field(
        default_factory=dict, 
        description="JSON schema defining the expected parameters for execution"
    )


class BaseSkill(ABC):
    """
    Abstract base class for all GLaDOS skills.
    Every skill must provide its definition and an async execution method.
    """

    @property
    @abstractmethod
    def definition(self) -> SkillDefinition:
        """Returns the metadata definition of this skill."""
        pass

    @abstractmethod
    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the skill's logic.
        
        :param ctx: The global runtime context (provides access to memory, logger, etc.).
        :param params: Validated parameters for this specific execution.
        :return: The result of the execution.
        """
        pass