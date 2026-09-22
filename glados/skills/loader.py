# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class Skill:
    """Lightweight skill representation for dynamically loaded modules."""
    name: str
    description: str
    handler: Any


class SkillLoader:
    """
    Dynamically discovers and loads skill modules from a directory.
    Each valid module must expose 'name', 'description', and 'handler' attributes.
    """

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir
        self.logger = logger.bind(component="SkillLoader")
        self.logger.debug(f"SkillLoader initialized with dir: {skills_dir}")

    def load_all(self, registry: Any) -> int:
        """
        Scans the skills directory and registers all valid skill modules.
        
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
                skill = self._load_module(skill_file)
                if skill:
                    registry.register(skill)
                    loaded_count += 1
                    self.logger.debug(f"Loaded skill: {skill.name} from {skill_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to load skill from {skill_file.name}: {e}")

        self.logger.info(f"SkillLoader completed: {loaded_count} skill(s) loaded")
        return loaded_count

    def _load_module(self, skill_file: Path) -> Skill | None:
        """Dynamically imports a single skill module and extracts its attributes."""
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

        name = getattr(module, "name", None)
        description = getattr(module, "description", None)
        handler = getattr(module, "handler", None)

        if not name or not description or not handler:
            missing = [attr for attr, val in [("name", name), ("description", description), ("handler", handler)] if not val]
            raise ValueError(f"Missing required attributes: {missing}")

        return Skill(name=name, description=description, handler=handler)