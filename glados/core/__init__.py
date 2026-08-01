# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Core package of GLaDOS.

Contains the central agent implementation and core interfaces.
"""

from .agent import GLaDOSAgent
from .identity import Identity

__all__ = [
    "GLaDOSAgent",
    "Identity",
]
