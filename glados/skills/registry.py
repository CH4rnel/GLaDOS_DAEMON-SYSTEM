# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import Any, Dict, List

from loguru import logger


class SkillNotFoundError(Exception):
    """Raised when a requested skill is not found in the registry."""
    pass


class SkillRegistry:
    """
    Central registry for all available skills.
    Provides registration, discovery, and retrieval of skills by name.
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Any] = {}
        self.logger = logger.bind(component="SkillRegistry")
        self.logger.debug("SkillRegistry initialized")

    def register(self, skill: Any) -> None:
        """Registers a new skill. Raises ValueError if name already exists."""
        name = getattr(skill, "name", None)
        if not name:
            raise ValueError("Skill object must have a 'name' attribute.")
            
        if name in self._skills:
            raise ValueError(f"Skill '{name}' is already registered.")
            
        self._skills[name] = skill
        self.logger.debug(f"Registered skill: {name}")

    def get(self, name: str) -> Any:
        """Retrieves a skill by name. Raises SkillNotFoundError if not found."""
        if name not in self._skills:
            raise SkillNotFoundError(f"Skill '{name}' not found in registry.")
        return self._skills[name]

    def list_all(self) -> List[Any]:
        """Returns all registered skills."""
        return list(self._skills.values())

    def unregister(self, name: str) -> None:
        """Removes a skill from the registry."""
        if name in self._skills:
            del self._skills[name]
            self.logger.debug(f"Unregistered skill: {name}")