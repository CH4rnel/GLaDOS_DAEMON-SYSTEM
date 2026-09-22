# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass

from glados.skills.registry import SkillRegistry, SkillNotFoundError


@dataclass
class MockSkill:
    name: str
    description: str
    handler: MagicMock


class TestSkillRegistry:
    def setup_method(self) -> None:
        self.registry = SkillRegistry()

    def test_registry_initialization(self) -> None:
        assert self.registry is not None
        assert len(self.registry.list_all()) == 0

    def test_register_skill_successfully(self) -> None:
        skill = MockSkill(
            name="summarize_text",
            description="Summarizes long text into key points",
            handler=MagicMock()
        )
        self.registry.register(skill)
        
        skills = self.registry.list_all()
        assert len(skills) == 1
        assert skills[0].name == "summarize_text"

    def test_register_duplicate_skill_raises_error(self) -> None:
        skill1 = MockSkill(name="summarize_text", description="First", handler=MagicMock())
        skill2 = MockSkill(name="summarize_text", description="Second", handler=MagicMock())
        
        self.registry.register(skill1)
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register(skill2)

    def test_get_skill_by_name(self) -> None:
        skill = MockSkill(name="extract_keywords", description="Extracts keywords", handler=MagicMock())
        self.registry.register(skill)
        
        retrieved = self.registry.get("extract_keywords")
        assert retrieved is not None
        assert retrieved.name == "extract_keywords"

    def test_get_nonexistent_skill_raises_error(self) -> None:
        with pytest.raises(SkillNotFoundError, match="not found in registry"):
            self.registry.get("nonexistent_skill")

    def test_list_all_returns_all_registered_skills(self) -> None:
        skill1 = MockSkill(name="skill_one", description="First", handler=MagicMock())
        skill2 = MockSkill(name="skill_two", description="Second", handler=MagicMock())
        
        self.registry.register(skill1)
        self.registry.register(skill2)
        
        skills = self.registry.list_all()
        assert len(skills) == 2
        skill_names = [s.name for s in skills]
        assert "skill_one" in skill_names
        assert "skill_two" in skill_names