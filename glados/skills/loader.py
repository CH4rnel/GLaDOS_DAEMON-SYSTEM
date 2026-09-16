# glados/skills/loader.py
# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Skill loader for dynamic skill discovery and registration.
Scans the skills directory and loads all available skills into the registry.
"""

import importlib
import inspect
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from glados.skills.base import BaseSkill

if TYPE_CHECKING:
    from glados.skills.registry import SkillRegistry


class SkillLoader:
    """
    Dynamic loader for skills.
    Scans a directory for Python modules containing BaseSkill subclasses
    and registers them in the SkillRegistry.
    """
    
    def __init__(self, skills_dir: str | Path = "glados/skills/builtin") -> None:
        """
        Initialize the skill loader.
        
        :param skills_dir: Directory containing skill modules
        """
        self.skills_dir = Path(skills_dir)
        self.logger = logger.bind(component="SkillLoader")
    
    def load_all(self, registry: "SkillRegistry") -> int:
        """
        Load all skills from the skills directory into the registry.
        
        :param registry: SkillRegistry instance to register skills into
        :return: Number of successfully loaded skills
        """
        if not self.skills_dir.exists():
            self.logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return 0
        
        loaded_count = 0
        
        # Scan for Python files in the skills directory
        for skill_file in self.skills_dir.glob("*.py"):
            if skill_file.name.startswith("_"):
                continue  # Skip __init__.py and private modules
            
            try:
                count = self._load_module(skill_file, registry)
                loaded_count += count
            except Exception as e:
                self.logger.error(f"Failed to load skill from {skill_file}: {e}")
        
        self.logger.info(f"Loaded {loaded_count} skills from {self.skills_dir}")
        return loaded_count
    
    def _load_module(self, module_path: Path, registry: "SkillRegistry") -> int:
        """
        Load a single Python module and register all BaseSkill subclasses.
        
        :param module_path: Path to the Python module
        :param registry: SkillRegistry instance
        :return: Number of skills registered from this module
        """
        # Convert file path to module name
        # e.g., glados/skills/builtin/echo.py -> glados.skills.builtin.echo
        relative_path = module_path.relative_to(self.skills_dir.parent.parent.parent)
        module_name = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]  # Remove .py
        
        try:
            # Dynamically import the module
            module = importlib.import_module(module_name)
            
            # Find all BaseSkill subclasses in the module
            registered_count = 0
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    try:
                        # Instantiate the skill
                        skill_instance = obj()
                        
                        # Register it
                        registry.register(skill_instance)
                        registered_count += 1
                        
                        self.logger.debug(f"Registered skill: {skill_instance.definition.name} from {module_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to register skill {name} from {module_name}: {e}")
            
            return registered_count
            
        except Exception as e:
            self.logger.error(f"Failed to import module {module_name}: {e}")
            raise