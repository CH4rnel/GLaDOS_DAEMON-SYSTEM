# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
MCP Client implementation for connecting to external MCP servers.
Supports stdio and SSE transports with GuardianGate audit integration.
"""

from typing import Any, Optional
from contextlib import AsyncExitStack
from loguru import logger

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from glados.mcp.models import MCPClientConfig, MCPTool, TransportType


class MCPClient:
    """
    Client for a single MCP server connection.
    Handles tool discovery and invocation with security auditing.
    """

    def __init__(self, config: MCPClientConfig, guardian: Optional[Any] = None):
        self.config = config
        self.guardian = guardian
        self.session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()
        self.logger = logger.bind(component="MCPClient", server=config.name)

    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        self.logger.info(f"Connecting to MCP server via {self.config.transport.value}")
        
        if self.config.transport == TransportType.STDIO:
            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env or None,
            )
            read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
        elif self.config.transport == TransportType.SSE:
            read, write = await self._exit_stack.enter_async_context(sse_client(self.config.url))
        else:
            raise ValueError(f"Unsupported transport: {self.config.transport}")
        
        self.session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        self.logger.info(f"Connected to MCP server: {self.config.name}")

    async def disconnect(self) -> None:
        """Close connection to the MCP server."""
        await self._exit_stack.aclose()
        self.logger.info(f"Disconnected from MCP server: {self.config.name}")

    async def list_tools(self) -> list[MCPTool]:
        """Retrieve list of available tools from the server."""
        if not self.session:
            raise RuntimeError("Client not connected")
        
        response = await self.session.list_tools()
        tools = [
            MCPTool(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.input_schema,
                server_name=self.config.name,
            )
            for tool in response.tools
        ]
        self.logger.debug(f"Discovered {len(tools)} tools from {self.config.name}")
        return tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Invoke a tool on the MCP server.
        Audits the call through GuardianGate if available.
        """
        # GuardianGate audit: authorize BEFORE checking session (fail-fast)
        if self.guardian:
            if not self.guardian.authorize_tool_call(
                tool_name=tool_name,
                server_name=self.config.name,
                arguments=arguments,
            ):
                self.guardian.log_audit(
                    action="MCP_TOOL_CALL",
                    status="DENIED",
                    details=f"{self.config.name}:{tool_name}",
                )
                raise PermissionError(f"Tool call denied by GuardianGate: {tool_name}")
        
        if not self.session:
            raise RuntimeError("Client not connected")
        
        self.logger.info(f"Calling MCP tool: {self.config.name}:{tool_name}")
        response = await self.session.call_tool(tool_name, arguments)
        
        # GuardianGate audit: log successful execution
        if self.guardian:
            self.guardian.log_audit(
                action="MCP_TOOL_CALL",
                status="ALLOWED",
                details=f"{self.config.name}:{tool_name}",
            )
        
        return [content.model_dump() if hasattr(content, "model_dump") else content 
                for content in response.content]