# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS Tool subsystem.
Follows TDD methodology (Red -> Green -> Refactor) to define the contract for Tools.
"""

import pytest
from typing import Any

# These imports will fail initially (Red Phase)
from glados.tools.base import ToolDefinition, BaseTool
from glados.tools.registry import ToolRegistry, ToolNotFoundError
from glados.core.context import RuntimeContext


class MockTool(BaseTool):
    """A mock tool for testing the registry."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={"query": "str"}
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        return f"Mock tool executed with: {params.get('query')}"


class TestToolDefinition:
    """Tests for the ToolDefinition Pydantic model."""

    def test_tool_definition_creation(self):
        """Test creating a valid tool definition."""
        defn = ToolDefinition(name="test_tool", description="Test tool")
        assert defn.name == "test_tool"
        assert defn.parameters == {}

    def test_tool_definition_invalid_name(self):
        """Test that empty name raises ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ToolDefinition(name="", description="Invalid")


class TestToolRegistry:
    """Tests for the ToolRegistry."""

    def test_register_and_get_tool(self):
        """Test registering a tool and retrieving it by name."""
        registry = ToolRegistry()
        tool = MockTool()
        
        registry.register(tool)
        retrieved = registry.get("mock_tool")
        
        assert retrieved is tool
        assert retrieved.definition.name == "mock_tool"

    def test_get_nonexistent_tool_raises_error(self):
        """Test that getting an unregistered tool raises ToolNotFoundError."""
        registry = ToolRegistry()
        
        with pytest.raises(ToolNotFoundError):
            registry.get("nonexistent_tool")

    def test_register_duplicate_tool_raises_error(self):
        """Test that registering a tool with an existing name raises ValueError."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = MockTool() # Same name "mock_tool"
        
        registry.register(tool1)
        
        with pytest.raises(ValueError):
            registry.register(tool2)

    def test_list_all_tools(self):
        """Test listing all registered tool definitions."""
        registry = ToolRegistry()
        registry.register(MockTool())
        
        definitions = registry.list_all()
        assert len(definitions) == 1
        assert definitions[0].name == "mock_tool"