# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the MCP Client implementation.
Covers configuration loading, client initialization, tool discovery,
and GuardianGate integration for tool invocation auditing.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from glados.mcp.models import MCPClientConfig, MCPTool, TransportType
from glados.mcp.client import MCPClient
from glados.mcp.manager import MCPClientManager


class TestMCPClientConfig:
    """Tests for MCP client configuration parsing."""

    def test_load_config_from_yaml(self, tmp_path: Path):
        """Test that MCP client config is correctly parsed from YAML."""
        config_content = """
clients:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    enabled: true
  - name: github
    transport: sse
    url: http://localhost:3001/sse
    enabled: false
"""
        config_file = tmp_path / "mcp_clients.yaml"
        config_file.write_text(config_content)

        manager = MCPClientManager()
        configs = manager.load_config(config_file)

        assert len(configs) == 2
        
        fs_config = next(c for c in configs if c.name == "filesystem")
        assert fs_config.transport == TransportType.STDIO
        assert fs_config.command == "npx"
        assert fs_config.enabled is True
        
        gh_config = next(c for c in configs if c.name == "github")
        assert gh_config.transport == TransportType.SSE
        assert gh_config.url == "http://localhost:3001/sse"
        assert gh_config.enabled is False


class TestMCPClient:
    """Tests for individual MCP client behavior."""

    @pytest.mark.asyncio
    async def test_client_connect_and_list_tools(self):
        """Test that client connects and retrieves tool list."""
        config = MCPClientConfig(
            name="test-server",
            transport=TransportType.STDIO,
            command="echo",
            args=["test"],
            enabled=True,
        )
        
        mock_tools = [
            MCPTool(name="read_file", description="Read a file", input_schema={}),
            MCPTool(name="write_file", description="Write a file", input_schema={}),
        ]
        
        with patch("glados.mcp.client.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.list_tools.return_value = MagicMock(tools=mock_tools)
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            
            client = MCPClient(config)
            await client.connect()
            tools = await client.list_tools()
            
            assert len(tools) == 2
            assert tools[0].name == "read_file"
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_client_call_tool_with_guardian_audit(self):
        """Test that tool calls are audited through GuardianGate."""
        config = MCPClientConfig(
            name="test-server",
            transport=TransportType.STDIO,
            command="echo",
            args=["test"],
            enabled=True,
        )
        
        with patch("glados.mcp.client.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.call_tool.return_value = MagicMock(content=[{"type": "text", "text": "result"}])
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            
            mock_guardian = MagicMock()
            mock_guardian.authorize_tool_call.return_value = True
            
            client = MCPClient(config, guardian=mock_guardian)
            await client.connect()
            
            result = await client.call_tool("read_file", {"path": "/tmp/test.txt"})
            
            assert result == [{"type": "text", "text": "result"}]
            mock_guardian.authorize_tool_call.assert_called_once()
            mock_guardian.log_audit.assert_called_once()
            
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_client_call_tool_denied_by_guardian(self):
        """Test that tool calls denied by GuardianGate are blocked."""
        config = MCPClientConfig(
            name="test-server",
            transport=TransportType.STDIO,
            command="echo",
            args=["test"],
            enabled=True,
        )
        
        mock_guardian = MagicMock()
        mock_guardian.authorize_tool_call.return_value = False
        
        client = MCPClient(config, guardian=mock_guardian)
        
        with pytest.raises(PermissionError):
            await client.call_tool("dangerous_tool", {})


class TestMCPClientManager:
    """Tests for the MCP client manager."""

    @pytest.mark.asyncio
    async def test_manager_initializes_enabled_clients(self, tmp_path: Path):
        """Test that manager only initializes enabled clients."""
        config_content = """
clients:
  - name: fs-enabled
    transport: stdio
    command: echo
    args: ["test"]
    enabled: true
  - name: fs-disabled
    transport: stdio
    command: echo
    args: ["test"]
    enabled: false
"""
        config_file = tmp_path / "mcp_clients.yaml"
        config_file.write_text(config_content)

        manager = MCPClientManager()
        
        with patch("glados.mcp.manager.MCPClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.list_tools.return_value = []
            mock_client_cls.return_value = mock_client
            
            await manager.initialize(config_file)
            
            assert len(manager.clients) == 1
            assert "fs-enabled" in manager.clients
            assert "fs-disabled" not in manager.clients

    @pytest.mark.asyncio
    async def test_manager_aggregates_tools_from_all_clients(self, tmp_path: Path):
        """Test that manager aggregates tools from all connected clients."""
        config_content = """
clients:
  - name: server1
    transport: stdio
    command: echo
    args: ["test"]
    enabled: true
"""
        config_file = tmp_path / "mcp_clients.yaml"
        config_file.write_text(config_content)

        manager = MCPClientManager()
        
        mock_tools = [
            MCPTool(name="tool_a", description="Tool A", input_schema={}),
            MCPTool(name="tool_b", description="Tool B", input_schema={}),
        ]
        
        with patch("glados.mcp.manager.MCPClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.list_tools.return_value = mock_tools
            mock_client_cls.return_value = mock_client
            
            await manager.initialize(config_file)
            all_tools = await manager.list_all_tools()
            
            assert len(all_tools) == 2
            assert any(t.name == "tool_a" for t in all_tools)