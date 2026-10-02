# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the MCP Server implementation.
Covers tool listing, tool invocation routing through GuardianGate,
and security policy enforcement for external MCP clients.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from glados.mcp.server import build_mcp_server
from glados.tools.base import BaseTool, ToolDefinition
from glados.tools.registry import ToolRegistry
from glados.security.guardian import GuardianGate
import mcp.types as types


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, description: str = "Mock tool"):
        self._definition = ToolDefinition(
            name=name,
            description=description,
            parameters={"type": "object", "properties": {}},
        )
    
    @property
    def definition(self) -> ToolDefinition:
        return self._definition
    
    async def execute(self, ctx, params: dict):
        return f"Result from {self._definition.name}"


class TestMCPServer:
    """Tests for MCP server tool listing and invocation."""

    @pytest.mark.asyncio
    async def test_list_tools_exposes_registry(self):
        """Test that list_tools exposes all tools from ToolRegistry."""
        registry = ToolRegistry()
        tool_a = MockTool("search_memory", "Search long-term memory")
        tool_b = MockTool("get_system_status", "Get system resource status")
        registry.register(tool_a)
        registry.register(tool_b)
        
        guardian = MagicMock(spec=GuardianGate)
        ctx = MagicMock()
        
        server = build_mcp_server(registry, guardian, ctx)
        tools = await server._list_tools_handler()
        
        assert len(tools) == 2
        assert any(t.name == "search_memory" for t in tools)
        assert any(t.name == "get_system_status" for t in tools)

    @pytest.mark.asyncio
    async def test_call_tool_routes_through_guardian(self):
        """Test that tool calls are routed through GuardianGate for audit."""
        registry = ToolRegistry()
        tool = MockTool("search_memory", "Search long-term memory")
        registry.register(tool)
        
        guardian = MagicMock(spec=GuardianGate)
        guardian.execute = AsyncMock(return_value="Search results")
        
        ctx = MagicMock()
        server = build_mcp_server(registry, guardian, ctx)
        
        result = await server._call_tool_handler("search_memory", {"query": "test"})
        
        guardian.execute.assert_called_once_with("search_memory", ctx, {"query": "test"})
        # MCP protocol returns a list of TextContent objects
        assert result == [types.TextContent(type="text", text="Search results")]

    @pytest.mark.asyncio
    async def test_call_tool_denied_by_guardian(self):
        """Test that tool calls denied by GuardianGate are blocked."""
        registry = ToolRegistry()
        tool = MockTool("dangerous_tool", "Dangerous operation")
        registry.register(tool)
        
        guardian = MagicMock(spec=GuardianGate)
        guardian.execute = AsyncMock(side_effect=PermissionError("Tool call denied"))
        
        ctx = MagicMock()
        server = build_mcp_server(registry, guardian, ctx)
        
        with pytest.raises(PermissionError, match="Tool call denied"):
            await server._call_tool_handler("dangerous_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_not_found_in_registry(self):
        """Test that calling a non-existent tool raises appropriate error."""
        registry = ToolRegistry()
        guardian = MagicMock(spec=GuardianGate)
        ctx = MagicMock()
        
        server = build_mcp_server(registry, guardian, ctx)
        
        with pytest.raises(Exception):
            await server._call_tool_handler("nonexistent_tool", {})