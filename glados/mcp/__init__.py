# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
MCP (Model Context Protocol) integration for GLaDOS.
Provides client and manager for connecting to external MCP servers.
"""

from glados.mcp.models import MCPClientConfig, MCPTool, TransportType
from glados.mcp.client import MCPClient
from glados.mcp.manager import MCPClientManager

__all__ = ["MCPClientConfig", "MCPTool", "TransportType", "MCPClient", "MCPClientManager"]