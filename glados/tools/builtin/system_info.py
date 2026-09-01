# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in System Info Tool.
Provides basic operating system and environment information.
"""

import platform
from typing import Any

from glados.core.context import RuntimeContext
from glados.tools.base import BaseTool, ToolDefinition


class SystemInfoTool(BaseTool):
    """
    A basic tool that returns system information (OS, architecture, Python version).
    Useful for the agent to understand its execution environment.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_system_info",
            description="Retrieves basic information about the host operating system and Python environment.",
            parameters={
                "type": "object",
                "properties": {
                    "detail_level": {
                        "type": "string",
                        "enum": ["basic", "detailed"],
                        "description": "Level of detail to return",
                        "default": "basic"
                    }
                }
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the system info retrieval logic.
        
        :param ctx: Runtime context (used for logging).
        :param params: Dictionary containing optional 'detail_level'.
        :return: Dictionary with system information.
        """
        detail_level = params.get("detail_level", "basic")
        ctx.logger.debug(f"SystemInfoTool executing with detail_level: {detail_level}")
        
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "node": platform.node()
        }
        
        if detail_level == "detailed":
            info["processor"] = platform.processor()
            info["platform"] = platform.platform()
            
        return info