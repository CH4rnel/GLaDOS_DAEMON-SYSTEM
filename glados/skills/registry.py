# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Skill Registry for GLaDOS_DAEMON-SYSTEM.
Acts as a central catalog for all available skills.
"""

from loguru import logger

from glados.skills.base import BaseSkill, SkillDefinition


class SkillNotFoundError(Exception):
    """Raised when a requested skill is not found in the registry."""
    pass


class SkillRegistry:
    """
    Central registry for managing and retrieving skills.
    Ensures skill names are unique and provides a unified interface for the Brain.
    """

    def __init__(self) -> None:
        """Initializes the empty skill registry."""
        self._skills: dict[str, BaseSkill] = {}
        self.logger = logger.bind(component="SkillRegistry")
        self.logger.debug("SkillRegistry initialized.")

    def register(self, skill: BaseSkill) -> None:
        """
        Registers a new skill in the registry.
        
        :param skill: The skill instance to register.
        :raises ValueError: If a skill with the same name is already registered.
        """
        name = skill.definition.name
        
        if name in self._skills:
            raise ValueError(f"Skill with name '{name}' is already registered.")
            
        self._skills[name] = skill
        self.logger.info(f"Registered skill: {name}")

    def get(self, name: str) -> BaseSkill:
        """
        Retrieves a skill by its unique name.
        
        :param name: The name of the skill.
        :return: The skill instance.
        :raises SkillNotFoundError: If the skill is not registered.
        """
        if name not in self._skills:
            raise SkillNotFoundError(f"Skill '{name}' not found in registry.")
            
        return self._skills[name]

    def list_all(self) -> list[SkillDefinition]:
        """
        Returns a list of definitions for all registered skills.
        Useful for LLM context injection or CLI listing.
        """
        return [skill.definition for skill in self._skills.values()]