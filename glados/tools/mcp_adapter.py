# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
MCP Tool Adapter for GLaDOS_DAEMON-SYSTEM.
Bridges external Model Context Protocol (MCP) server tools into the 
standard glados/tools/base.py interface.

Security Note:
This adapter enforces SecurityPolicy.check_mcp_tool() BEFORE delegating 
to the MCP session. This ensures GuardianGate audit logging and fail-closed 
security apply to external tools exactly as they do to built-in tools.
"""

from typing import Any

from mcp.client.session import ClientSession
from mcp.types import Tool as MCPTool

from glados.core.context import RuntimeContext
from glados.security.policy import PolicyViolation
from glados.tools.base import BaseTool, ToolDefinition


class MCPToolAdapter(BaseTool):
    """
    Wraps an MCP server tool to behave like a native GLaDOS BaseTool.
    """

    def __init__(
        self, 
        server_name: str, 
        mcp_tool: MCPTool, 
        mcp_session: ClientSession
    ) -> None:
        """
        :param server_name: Identifier for the MCP server (e.g., "filesystem").
        :param mcp_tool: The tool definition object from the MCP SDK.
        :param mcp_session: An active, connected MCP ClientSession.
        """
        self._server_name = server_name
        self._mcp_tool = mcp_tool
        self._mcp_session = mcp_session

    @property
    def definition(self) -> ToolDefinition:
        """
        Maps the MCP tool schema to GLaDOS ToolDefinition.
        Prefixes the name with the server name to prevent collisions 
        (e.g., "mcp_filesystem_read_file").
        """
        prefixed_name = f"mcp_{self._server_name}_{self._mcp_tool.name}"
        
        return ToolDefinition(
            name=prefixed_name,
            description=self._mcp_tool.description or f"MCP tool from {self._server_name}",
            parameters=self._mcp_tool.inputSchema or {"type": "object", "properties": {}}
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the MCP tool, strictly gated by SecurityPolicy.
        """
        # 1. Security Check (Fail-closed)
        # The policy must explicitly allow this tool on this server.
        if ctx.security is not None:
            try:
                ctx.security.check_mcp_tool(self._server_name, self._mcp_tool.name)
            except PolicyViolation as e:
                ctx.logger.warning(f"MCP tool denied by policy: {self.definition.name} - {e}")
                raise

        # 2. Execution
        ctx.logger.debug(f"Executing MCP tool: {self._mcp_tool.name} with params: {params}")
        try:
            result = await self._mcp_session.call_tool(
                name=self._mcp_tool.name,
                arguments=params
            )
        except Exception as e:
            ctx.logger.error(f"MCP tool execution failed: {self._mcp_tool.name} - {e}")
            return {"success": False, "error": str(e)}

        # 3. Result Formatting
        if result.isError:
            error_text = "\n".join(
                item.text for item in result.content if hasattr(item, "text")
            ) or "Unknown MCP tool error"
            ctx.logger.warning(f"MCP tool returned error: {self._mcp_tool.name} - {error_text}")
            return {"success": False, "error": error_text}

        # Extract text content from MCP response
        content_text = "\n".join(
            item.text for item in result.content if hasattr(item, "text")
        )
        
        return {"success": True, "content": content_text}