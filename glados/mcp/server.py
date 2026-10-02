# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
MCP Server implementation for exposing GLaDOS tools to external MCP clients.
Routes all tool invocations through GuardianGate for unified audit and security.
Compatible with MCP SDK v2.x and real ToolRegistry contract.
"""

from typing import Any
from loguru import logger

from mcp.server.mcpserver import MCPServer
import mcp.types as types

from glados.tools.registry import ToolRegistry, ToolNotFoundError
from glados.security.guardian import GuardianGate


def build_mcp_server(registry: ToolRegistry, guardian: GuardianGate, ctx: Any) -> MCPServer:
    """
    Build an MCP server that exposes GLaDOS tools to external clients.
    All tool calls are routed through GuardianGate for audit and security enforcement.
    """
    mcp = MCPServer("glados-daemon")
    logger.info("Building MCP server for GLaDOS tools")
    
    async def list_tools_handler() -> list[types.Tool]:
        """Expose all tools from ToolRegistry as MCP tools."""
        tools = [
            types.Tool(
                name=tool_def.name,
                description=tool_def.description,
                inputSchema=tool_def.parameters,
            )
            for tool_def in registry.list_all()
        ]
        logger.debug(f"Exposing {len(tools)} tools to MCP clients")
        return tools
    
    async def call_tool_handler(name: str, arguments: dict) -> list[types.TextContent]:
        """
        Invoke a tool through GuardianGate.
        External MCP clients receive the same audit trail as internal BrainEngine calls.
        """
        # Verify tool exists in registry (raises ToolNotFoundError if not)
        registry.get(name)
        
        logger.info(f"MCP client calling tool: {name}")
        
        # Route through GuardianGate for security and audit
        result = await guardian.execute(name, ctx, arguments)
        
        logger.debug(f"Tool {name} executed successfully via MCP")
        return [types.TextContent(type="text", text=str(result))]
    
    # Store handlers for testing
    mcp._list_tools_handler = list_tools_handler
    mcp._call_tool_handler = call_tool_handler
    
    # Dynamically register tools for actual MCP protocol handling
    for tool_def in registry.list_all():
        tool_name = tool_def.name
        
        def make_executor(t_name: str):
            async def executor(**kwargs: Any) -> str:
                logger.info(f"MCP client calling tool: {t_name}")
                result = await guardian.execute(t_name, ctx, kwargs)
                return str(result)
            executor.__name__ = t_name
            executor.__doc__ = next((t.description for t in registry.list_all() if t.name == t_name), "")
            return executor
            
        executor = make_executor(tool_name)
        mcp.tool()(executor)
    
    return mcp


async def run_stdio(registry: ToolRegistry, guardian: GuardianGate, ctx: Any) -> None:
    """
    Run the MCP server over stdio transport.
    Main entry point for the `glados mcp-serve` CLI command.
    """
    mcp = build_mcp_server(registry, guardian, ctx)
    logger.info("Starting MCP server on stdio transport")
    await mcp.run()