# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tool Registry for GLaDOS_DAEMON-SYSTEM.
Acts as a central catalog for all available low-level tools.
"""

from loguru import logger

from glados.tools.base import BaseTool, ToolDefinition


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not found in the registry."""
    pass


class ToolRegistry:
    """
    Central registry for managing and retrieving tools.
    Ensures tool names are unique and provides a unified interface for the Brain/Skills.
    """

    def __init__(self) -> None:
        """Initializes the empty tool registry."""
        self._tools: dict[str, BaseTool] = {}
        self.logger = logger.bind(component="ToolRegistry")
        self.logger.debug("ToolRegistry initialized.")

    def register(self, tool: BaseTool) -> None:
        """
        Registers a new tool in the registry.
        
        :param tool: The tool instance to register.
        :raises ValueError: If a tool with the same name is already registered.
        """
        name = tool.definition.name
        
        if name in self._tools:
            raise ValueError(f"Tool with name '{name}' is already registered.")
            
        self._tools[name] = tool
        self.logger.info(f"Registered tool: {name}")

    def get(self, name: str) -> BaseTool:
        """
        Retrieves a tool by its unique name.
        
        :param name: The name of the tool.
        :return: The tool instance.
        :raises ToolNotFoundError: If the tool is not registered.
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")
            
        return self._tools[name]

    def list_all(self) -> list[ToolDefinition]:
        """
        Returns a list of definitions for all registered tools.
        Useful for LLM context injection or CLI listing.
        """
        return [tool.definition for tool in self._tools.values()]