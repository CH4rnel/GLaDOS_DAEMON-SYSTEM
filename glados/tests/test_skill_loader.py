# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
import tempfile
from pathlib import Path

from glados.skills.registry import SkillRegistry
from glados.skills.loader import SkillLoader


class TestSkillLoader:
    def setup_method(self) -> None:
        self.registry = SkillRegistry()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.loader = SkillLoader(skills_dir=Path(self.temp_dir.name))

    def teardown_method(self) -> None:
        self.temp_dir.cleanup()

    def test_loader_initialization(self) -> None:
        assert self.loader is not None
        assert self.loader.skills_dir.exists()

    def test_load_all_from_empty_directory(self) -> None:
        self.loader.load_all(self.registry)
        assert len(self.registry.list_all()) == 0

    def test_load_valid_skill_module(self) -> None:
        # Create a mock skill module file using BaseSkill architecture
        skill_file = Path(self.temp_dir.name) / "test_skill.py"
        skill_file.write_text(
            "from glados.skills.base import BaseSkill, SkillDefinition\n"
            "from glados.core.context import RuntimeContext\n"
            "from typing import Any\n"
            "\n"
            "class TestSkill(BaseSkill):\n"
            "    @property\n"
            "    def definition(self) -> SkillDefinition:\n"
            "        return SkillDefinition(name='test_skill', description='A test skill', parameters={})\n"
            "    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:\n"
            "        return 'executed'\n"
        )

        self.loader.load_all(self.registry)

        skills = self.registry.list_all()
        assert len(skills) == 1
        assert skills[0].definition.name == "test_skill"

    def test_load_ignores_non_python_files(self) -> None:
        # Create a non-python file
        txt_file = Path(self.temp_dir.name) / "readme.txt"
        txt_file.write_text("This is not a skill")

        self.loader.load_all(self.registry)
        assert len(self.registry.list_all()) == 0

    def test_load_handles_malformed_skill_gracefully(self) -> None:
        # Create a module missing BaseSkill class
        bad_skill_file = Path(self.temp_dir.name) / "bad_skill.py"
        bad_skill_file.write_text(
            "name = 'bad_skill'\n"
            "description = 'Missing BaseSkill class'\n"
        )

        # Should not raise an exception, just log a warning and skip
        self.loader.load_all(self.registry)
        assert len(self.registry.list_all()) == 0