# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Runtime Context for GLaDOS_DAEMON-SYSTEM.
Provides shared state and dependencies across the application.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger
from glados.core.identity import Identity

if TYPE_CHECKING:
    from glados.memory.manager import MemoryManager
    from glados.skills.registry import SkillRegistry
    from glados.tools.registry import ToolRegistry

# Standard way to type-hint the loguru logger
LoggerType = type(logger)


@dataclass(slots=True)
class RuntimeContext:
    """
    Central container for runtime dependencies.
    Injected into core components to avoid global state.
    """
    identity: Identity
    logger: LoggerType
    memory: "MemoryManager" = field(default=None)  # type: ignore
    skills: "SkillRegistry" = field(default=None)  # type: ignore
    tools: "ToolRegistry" = field(default=None)  # type: ignore