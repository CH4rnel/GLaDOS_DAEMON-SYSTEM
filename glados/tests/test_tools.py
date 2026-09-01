# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS Tool subsystem.
Follows TDD methodology (Red -> Green -> Refactor) to define the contract for Tools.
Ensures strict validation, registry integrity, and execution correctness.
"""

import asyncio
from typing import Any

import pytest
from pydantic import ValidationError

from glados.core.context import RuntimeContext
from glados.tools.base import BaseTool, ToolDefinition
from glados.tools.registry import ToolNotFoundError, ToolRegistry


# -----------------------------------------------------------------------------
# Mock Implementations for Testing
# -----------------------------------------------------------------------------

class MockTool(BaseTool):
    """A mock tool for testing the registry and execution pipeline."""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={"query": "str"}
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        return f"Mock tool executed with: {params.get('query', 'default')}"


class FailingTool(BaseTool):
    """A mock tool that intentionally raises an exception during execution."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="failing_tool",
            description="A tool that always fails"
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        raise RuntimeError("Intentional tool failure for testing")


class MockRuntimeContext:
    """Minimal mock for RuntimeContext to satisfy type hints during testing."""
    class MockLogger:
        def debug(self, *args: Any, **kwargs: Any) -> None: pass
        def info(self, *args: Any, **kwargs: Any) -> None: pass
        
    logger = MockLogger()


# -----------------------------------------------------------------------------
# Tests for ToolDefinition (Pydantic Model)
# -----------------------------------------------------------------------------

class TestToolDefinition:
    """Tests for the ToolDefinition Pydantic model validation."""

    def test_tool_definition_creation_valid(self):
        """Test creating a valid tool definition with default parameters."""
        defn = ToolDefinition(name="test_tool", description="Test tool")
        assert defn.name == "test_tool"
        assert defn.description == "Test tool"
        assert defn.parameters == {}

    def test_tool_definition_creation_with_parameters(self):
        """Test creating a tool definition with custom JSON schema parameters."""
        params = {"type": "object", "properties": {"file_path": {"type": "string"}}}
        defn = ToolDefinition(name="read_file", description="Reads a file", parameters=params)
        assert defn.parameters == params

    def test_tool_definition_invalid_empty_name(self):
        """Test that an empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            ToolDefinition(name="", description="Invalid")

    def test_tool_definition_invalid_empty_description(self):
        """Test that an empty description raises ValidationError."""
        with pytest.raises(ValidationError):
            ToolDefinition(name="valid_name", description="")


# -----------------------------------------------------------------------------
# Tests for BaseTool (Abstract Base Class)
# -----------------------------------------------------------------------------

class TestBaseTool:
    """Tests for the BaseTool abstract contract."""

    def test_base_tool_cannot_be_instantiated(self):
        """Test that BaseTool is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool()  # type: ignore

    def test_base_tool_requires_definition_and_execute(self):
        """Test that a subclass must implement both definition and execute."""
        class IncompleteTool(BaseTool):
            pass

        with pytest.raises(TypeError):
            IncompleteTool()  # type: ignore


# -----------------------------------------------------------------------------
# Tests for ToolRegistry
# -----------------------------------------------------------------------------

class TestToolRegistry:
    """Tests for the ToolRegistry state management."""

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
        
        with pytest.raises(ToolNotFoundError, match="not found in registry"):
            registry.get("nonexistent_tool")

    def test_register_duplicate_tool_raises_error(self):
        """Test that registering a tool with an existing name raises ValueError."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = MockTool()  # Same name "mock_tool"
        
        registry.register(tool1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2)

    def test_list_all_tools_empty(self):
        """Test listing tools from an empty registry."""
        registry = ToolRegistry()
        assert registry.list_all() == []

    def test_list_all_tools_multiple(self):
        """Test listing all registered tool definitions."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(FailingTool())
        
        definitions = registry.list_all()
        assert len(definitions) == 2
        
        names = {defn.name for defn in definitions}
        assert names == {"mock_tool", "failing_tool"}


# -----------------------------------------------------------------------------
# Tests for Tool Execution (Async)
# -----------------------------------------------------------------------------

class TestToolExecution:
    """Tests for the asynchronous execution of tools."""

    def test_mock_tool_execution_success(self):
        """Test successful execution of a mock tool with parameters."""
        tool = MockTool()
        ctx = MockRuntimeContext()
        
        result = asyncio.run(tool.execute(ctx, {"query": "test_data"}))
        assert result == "Mock tool executed with: test_data"

    def test_mock_tool_execution_default_params(self):
        """Test execution with missing optional parameters."""
        tool = MockTool()
        ctx = MockRuntimeContext()
        
        result = asyncio.run(tool.execute(ctx, {}))
        assert result == "Mock tool executed with: default"

    def test_failing_tool_execution_raises_error(self):
        """Test that a failing tool correctly propagates exceptions."""
        tool = FailingTool()
        ctx = MockRuntimeContext()
        
        with pytest.raises(RuntimeError, match="Intentional tool failure"):
            asyncio.run(tool.execute(ctx, {}))