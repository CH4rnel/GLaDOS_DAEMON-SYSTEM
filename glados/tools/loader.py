# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tool Loader for GLaDOS_DAEMON-SYSTEM.
Responsible for dynamically discovering and loading tools from the filesystem.
"""

import importlib.util
import inspect
from pathlib import Path
from loguru import logger

from glados.tools.base import BaseTool
from glados.tools.registry import ToolRegistry


class ToolLoader:
    """
    Dynamically discovers and loads tools from a specified directory.
    Scans for Python files, imports them, and registers all BaseTool subclasses.
    """

    def __init__(self, search_path: Path) -> None:
        """
        Initializes the tool loader.
        
        :param search_path: Directory to scan for tool modules.
        """
        self.search_path = search_path
        self.logger = logger.bind(component="ToolLoader")
        self.logger.debug(f"ToolLoader initialized with path: {self.search_path}")

    def load_all(self, registry: ToolRegistry) -> int:
        """
        Scans the search path and loads all discovered tools into the registry.
        
        :param registry: The ToolRegistry instance to populate.
        :return: Number of successfully loaded tools.
        """
        if not self.search_path.exists() or not self.search_path.is_dir():
            self.logger.warning(f"Tool search path does not exist: {self.search_path}")
            return 0

        loaded_count = 0
        tool_files = self.search_path.glob("*.py")

        for file_path in tool_files:
            # Skip private modules and __init__.py
            if file_path.name.startswith("_"):
                continue

            try:
                count = self._load_module(file_path, registry)
                loaded_count += count
            except Exception as e:
                self.logger.error(f"Failed to load tool from {file_path}: {e}", exc_info=True)

        self.logger.info(f"ToolLoader completed. Loaded {loaded_count} tools from {self.search_path}")
        return loaded_count

    def _load_module(self, file_path: Path, registry: ToolRegistry) -> int:
        """
        Dynamically imports a single Python module and registers all BaseTool subclasses.
        
        :param file_path: Path to the Python file.
        :param registry: The ToolRegistry instance.
        :return: Number of tools registered from this module.
        """
        module_name = f"glados.tools.dynamic.{file_path.stem}"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            self.logger.warning(f"Could not create module spec for {file_path}")
            return 0

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        registered_count = 0
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseTool) and obj is not BaseTool:
                try:
                    tool_instance = obj()
                    registry.register(tool_instance)
                    registered_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to instantiate tool {name} from {file_path}: {e}")

        return registered_count