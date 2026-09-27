# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the MCP Tool Adapter.
Ensures external MCP tools are correctly mapped to BaseTool interface
and strictly enforced by SecurityPolicy via GuardianGate.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from pydantic import ValidationError

from glados.core.context import RuntimeContext
from glados.security.policy import PolicyViolation, SecurityPolicy
from glados.tools.mcp_adapter import MCPToolAdapter


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter implementation."""

    @pytest.fixture
    def mock_mcp_tool(self):
        """Simulates an MCP Tool object from the official SDK."""
        tool = MagicMock()
        tool.name = "read_file"
        tool.description = "Reads the contents of a file"
        tool.inputSchema = {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"}
            },
            "required": ["path"]
        }
        return tool

    @pytest.fixture
    def mock_ctx(self):
        """Simulates RuntimeContext with SecurityPolicy."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.security = MagicMock(spec=SecurityPolicy)
        # By default, allow the tool
        ctx.security.check_mcp_tool = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.fixture
    def mock_mcp_session(self):
        """Simulates an active MCP ClientSession."""
        session = AsyncMock()
        return session

    def test_adapter_initialization_and_definition_mapping(self, mock_mcp_tool, mock_mcp_session):
        """Test that MCP tool schema is correctly mapped to ToolDefinition."""
        adapter = MCPToolAdapter(
            server_name="filesystem",
            mcp_tool=mock_mcp_tool,
            mcp_session=mock_mcp_session
        )

        assert adapter.definition.name == "mcp_filesystem_read_file"
        assert "Reads the contents of a file" in adapter.definition.description
        assert adapter.definition.parameters == mock_mcp_tool.inputSchema

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_mcp_tool, mock_ctx, mock_mcp_session):
        """Test successful tool execution and result formatting."""
        # Mock successful MCP call response
        mock_result = MagicMock()
        mock_result.isError = False
        mock_result.content = [MagicMock(type="text", text="File contents here")]
        mock_mcp_session.call_tool = AsyncMock(return_value=mock_result)

        adapter = MCPToolAdapter(
            server_name="filesystem",
            mcp_tool=mock_mcp_tool,
            mcp_session=mock_mcp_session
        )

        result = await adapter.execute(mock_ctx, {"path": "/tmp/test.txt"})

        mock_mcp_session.call_tool.assert_called_once_with(
            name="read_file", 
            arguments={"path": "/tmp/test.txt"}
        )
        assert result == {"success": True, "content": "File contents here"}

    @pytest.mark.asyncio
    async def test_execute_blocked_by_policy(self, mock_mcp_tool, mock_ctx, mock_mcp_session):
        """Test that GuardianGate catches PolicyViolation from the adapter."""
        # Simulate policy denying this specific MCP tool
        mock_ctx.security.check_mcp_tool.side_effect = PolicyViolation(
            "MCP tool 'read_file' on server 'filesystem' is not in the allowlist."
        )

        adapter = MCPToolAdapter(
            server_name="filesystem",
            mcp_tool=mock_mcp_tool,
            mcp_session=mock_mcp_session
        )

        with pytest.raises(PolicyViolation) as exc_info:
            await adapter.execute(mock_ctx, {"path": "/etc/passwd"})

        assert "not in the allowlist" in str(exc_info.value)
        # Ensure MCP session was NEVER called
        mock_mcp_session.call_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_handles_mcp_error_response(self, mock_mcp_tool, mock_ctx, mock_mcp_session):
        """Test graceful handling of MCP tool returning an error."""
        mock_result = MagicMock()
        mock_result.isError = True
        mock_result.content = [MagicMock(type="text", text="Permission denied")]
        mock_mcp_session.call_tool = AsyncMock(return_value=mock_result)

        adapter = MCPToolAdapter(
            server_name="filesystem",
            mcp_tool=mock_mcp_tool,
            mcp_session=mock_mcp_session
        )

        result = await adapter.execute(mock_ctx, {"path": "/root/secret.txt"})

        assert result == {"success": False, "error": "Permission denied"}