# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS Skill subsystem.
Follows TDD methodology to define the contract for Skills and the SkillRegistry.
"""

import pytest
from typing import Any

# These imports will fail initially (Red Phase)
from glados.skills.base import SkillDefinition, BaseSkill
from glados.skills.registry import SkillRegistry, SkillNotFoundError
from glados.core.context import RuntimeContext


class MockSkill(BaseSkill):
    """A mock skill for testing the registry."""
    
    @property
    def definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="mock_skill",
            description="A mock skill for testing",
            parameters={"input_text": "str"}
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        return f"Mock executed with: {params.get('input_text')}"


class TestSkillDefinition:
    """Tests for the SkillDefinition Pydantic model."""

    def test_skill_definition_creation(self):
        """Test creating a valid skill definition."""
        defn = SkillDefinition(name="test", description="Test skill")
        assert defn.name == "test"
        assert defn.parameters == {}

    def test_skill_definition_invalid_name(self):
        """Test that empty name raises ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SkillDefinition(name="", description="Invalid")


class TestSkillRegistry:
    """Tests for the SkillRegistry."""

    def test_register_and_get_skill(self):
        """Test registering a skill and retrieving it by name."""
        registry = SkillRegistry()
        skill = MockSkill()
        
        registry.register(skill)
        retrieved = registry.get("mock_skill")
        
        assert retrieved is skill
        assert retrieved.definition.name == "mock_skill"

    def test_get_nonexistent_skill_raises_error(self):
        """Test that getting an unregistered skill raises SkillNotFoundError."""
        registry = SkillRegistry()
        
        with pytest.raises(SkillNotFoundError):
            registry.get("nonexistent_skill")

    def test_register_duplicate_skill_raises_error(self):
        """Test that registering a skill with an existing name raises ValueError."""
        registry = SkillRegistry()
        skill1 = MockSkill()
        skill2 = MockSkill() # Same name "mock_skill"
        
        registry.register(skill1)
        
        with pytest.raises(ValueError):
            registry.register(skill2)

    def test_list_all_skills(self):
        """Test listing all registered skill definitions."""
        registry = SkillRegistry()
        registry.register(MockSkill())
        
        definitions = registry.list_all()
        assert len(definitions) == 1
        assert definitions[0].name == "mock_skill"