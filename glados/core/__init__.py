# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Core package of GLaDOS.

Contains the central interfaces and runtime context.
"""

from .identity import Identity
from .context import RuntimeContext

__all__ = [
    "Identity",
    "RuntimeContext",
]