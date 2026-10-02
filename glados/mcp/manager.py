# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
MCP Client Manager for orchestrating multiple MCP server connections.
"""

from pathlib import Path
from typing import Any, Optional
import yaml
from loguru import logger

from glados.mcp.models import MCPClientConfig, MCPTool
from glados.mcp.client import MCPClient


class MCPClientManager:
    """
    Manages lifecycle of multiple MCP client connections.
    Aggregates tools from all connected servers.
    """

    def __init__(self, guardian: Optional[Any] = None):
        self.clients: dict[str, MCPClient] = {}
        self.guardian = guardian
        self.logger = logger.bind(component="MCPClientManager")

    def load_config(self, config_path: Path) -> list[MCPClientConfig]:
        """Load MCP client configurations from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        clients_data = data.get("clients", [])
        configs = [MCPClientConfig(**client) for client in clients_data]
        self.logger.info(f"Loaded {len(configs)} MCP client configurations")
        return configs

    async def initialize(self, config_path: Path) -> None:
        """Initialize and connect all enabled MCP clients."""
        configs = self.load_config(config_path)
        
        for config in configs:
            if not config.enabled:
                self.logger.debug(f"Skipping disabled MCP client: {config.name}")
                continue
            
            client = MCPClient(config, guardian=self.guardian)
            try:
                await client.connect()
                self.clients[config.name] = client
                self.logger.info(f"Initialized MCP client: {config.name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize MCP client {config.name}: {e}")

    async def shutdown(self) -> None:
        """Disconnect all MCP clients."""
        for name, client in self.clients.items():
            try:
                await client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting MCP client {name}: {e}")
        self.clients.clear()
        self.logger.info("All MCP clients disconnected")

    async def list_all_tools(self) -> list[MCPTool]:
        """Aggregate tools from all connected MCP clients."""
        all_tools: list[MCPTool] = []
        for client in self.clients.values():
            try:
                tools = await client.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                self.logger.error(f"Failed to list tools from {client.config.name}: {e}")
        self.logger.debug(f"Aggregated {len(all_tools)} tools from {len(self.clients)} MCP servers")
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> list[dict]:
        """Invoke a tool on a specific MCP server."""
        if server_name not in self.clients:
            raise ValueError(f"MCP server not found: {server_name}")
        return await self.clients[server_name].call_tool(tool_name, arguments)