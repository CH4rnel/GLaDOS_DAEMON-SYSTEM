# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Pydantic models for MCP client configuration and tools.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TransportType(str, Enum):
    """MCP transport protocol types."""
    STDIO = "stdio"
    SSE = "sse"


class MCPClientConfig(BaseModel):
    """Configuration for a single MCP client connection."""
    name: str
    transport: TransportType
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    url: Optional[str] = None
    enabled: bool = True
    env: dict[str, str] = Field(default_factory=dict)


class MCPTool(BaseModel):
    """Represents a tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: Optional[str] = None