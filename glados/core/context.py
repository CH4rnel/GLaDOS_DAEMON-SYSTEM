# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Runtime Context for GLaDOS_DAEMON-SYSTEM.
Provides shared state and dependencies across the application.
"""

from dataclasses import dataclass, field
from loguru import Logger

from glados.core.identity import Identity
from glados.memory.manager import MemoryManager


@dataclass(slots=True)
class RuntimeContext:
    """
    Central container for runtime dependencies.
    Injected into core components to avoid global state.
    """
    identity: Identity
    logger: Logger
    memory: MemoryManager = field(default=None) # Will be initialized in Agent