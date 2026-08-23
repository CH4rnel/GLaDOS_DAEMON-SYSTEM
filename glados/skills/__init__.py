# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Skill subsystem for GLaDOS_DAEMON-SYSTEM.
Provides the core contract, registry, and built-in skills for task execution.
"""

from glados.skills.base import BaseSkill, SkillDefinition
from glados.skills.registry import SkillRegistry, SkillNotFoundError

__all__ = [
    "BaseSkill",
    "SkillDefinition",
    "SkillRegistry",
    "SkillNotFoundError",
]