# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from glados.skills.base import BaseSkill
except ImportError:
    # Fallback for environments where base might not be fully resolved yet
    class BaseSkill:  # type: ignore
        pass


class SkillLoader:
    """
    Dynamically discovers and loads skill modules from a directory.
    Looks for classes inheriting from BaseSkill, instantiates them,
    and registers the instances in the SkillRegistry.
    """

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.logger = logger.bind(component="SkillLoader")
        self.logger.debug(f"SkillLoader initialized with dir: {skills_dir}")

    def load_all(self, registry: Any) -> int:
        """
        Scans the skills directory and registers all valid skill classes.
        
        :param registry: SkillRegistry instance to populate
        :return: Number of successfully loaded skills
        """
        if not self.skills_dir.exists():
            self.logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return 0

        loaded_count = 0
        for skill_file in sorted(self.skills_dir.glob("*.py")):
            if skill_file.name.startswith("_"):
                continue

            try:
                skill_instance = self._load_module(skill_file)
                if skill_instance:
                    registry.register(skill_instance)
                    loaded_count += 1
                    self.logger.debug(f"Loaded skill: {skill_instance.definition.name} from {skill_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to load skill from {skill_file.name}: {e}")

        self.logger.info(f"SkillLoader completed: {loaded_count} skill(s) loaded")
        return loaded_count

    def _load_module(self, skill_file: Path) -> Any | None:
        """Dynamically imports a single skill module and instantiates the BaseSkill class."""
        module_name = f"glados.skills.dynamic.{skill_file.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, skill_file)
        if spec is None or spec.loader is None:
            self.logger.debug(f"Could not create module spec for {skill_file}")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            sys.modules.pop(module_name, None)
            raise RuntimeError(f"Module execution failed: {e}") from e

        # Find all classes in the module that inherit from BaseSkill
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                # Instantiate the skill
                return obj()
        
        return None