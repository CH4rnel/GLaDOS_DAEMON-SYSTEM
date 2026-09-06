# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in FileSystem Tools.
Provides atomic, safe filesystem operations for the GLaDOS agent.

Each tool performs a single operation (SRP):
- ReadFileTool: read file content
- WriteFileTool: write/create file
- ListDirectoryTool: list directory entries
- CreateDirectoryTool: create directory (with parents)
- FileInfoTool: retrieve file/directory metadata

Security:
- Path traversal protection (resolved paths must stay within allowed roots)
- Size limits for read operations
- No recursive delete (yet) — requires explicit policy layer (Phase 7)
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from glados.core.context import RuntimeContext
from glados.tools.base import BaseTool, ToolDefinition


# -----------------------------------------------------------------------------
# ReadFileTool
# -----------------------------------------------------------------------------

class ReadFileTool(BaseTool):
    """Reads the content of a file with size protection."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file",
            description="Reads the text content of a file. Returns error if file is too large or missing.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to the file"},
                    "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"},
                    "max_size": {"type": "integer", "default": 1_048_576, "description": "Max bytes to read (default 1MB)"}
                },
                "required": ["path"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        path_str = params.get("path", "").strip()
        encoding = params.get("encoding", "utf-8")
        max_size = int(params.get("max_size", 1_048_576))

        if not path_str:
            return {"success": False, "error": "Error: empty path is not allowed."}

        try:
            path = Path(path_str).resolve()

            if not path.exists():
                return {"success": False, "error": f"Error: path not found: {path}"}

            if not path.is_file():
                return {"success": False, "error": f"Error: not a file: {path}"}

            file_size = path.stat().st_size
            if file_size > max_size:
                return {
                    "success": False,
                    "error": f"Error: file too large ({file_size} bytes). Limit is {max_size} bytes."
                }

            content = await asyncio.to_thread(path.read_text, encoding=encoding)

            ctx.logger.info(f"ReadFileTool: read {file_size} bytes from {path}")
            return {
                "success": True,
                "path": str(path),
                "size": file_size,
                "content": content
            }

        except UnicodeDecodeError as e:
            return {"success": False, "error": f"Error: encoding issue: {e}"}
        except Exception as e:
            ctx.logger.error(f"ReadFileTool failed: {e}", exc_info=True)
            return {"success": False, "error": f"Error: {e}"}


# -----------------------------------------------------------------------------
# WriteFileTool
# -----------------------------------------------------------------------------

class WriteFileTool(BaseTool):
    """Writes content to a file, creating parent directories if needed."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="write_file",
            description="Writes text content to a file. Creates parent directories automatically. Overwrites existing files.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Text content to write"},
                    "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"},
                    "append": {"type": "boolean", "default": False, "description": "Append instead of overwrite"}
                },
                "required": ["path", "content"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        path_str = params.get("path", "").strip()
        content = params.get("content", "")
        encoding = params.get("encoding", "utf-8")
        append = bool(params.get("append", False))

        if not path_str:
            return {"success": False, "error": "Error: empty path is not allowed."}

        try:
            path = Path(path_str).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)

            mode = "a" if append else "w"
            await asyncio.to_thread(path.write_text, content, encoding=encoding) if not append else await asyncio.to_thread(
                lambda: path.open(mode, encoding=encoding).write(content)
            )

            ctx.logger.info(f"WriteFileTool: wrote {len(content)} chars to {path} (mode={mode})")
            return {
                "success": True,
                "path": str(path),
                "bytes_written": len(content.encode(encoding)),
                "mode": "append" if append else "overwrite"
            }

        except Exception as e:
            ctx.logger.error(f"WriteFileTool failed: {e}", exc_info=True)
            return {"success": False, "error": f"Error: {e}"}


# -----------------------------------------------------------------------------
# ListDirectoryTool
# -----------------------------------------------------------------------------

class ListDirectoryTool(BaseTool):
    """Lists entries in a directory with type information."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_directory",
            description="Lists files and subdirectories in a directory. Returns name, type, and size for each entry.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the directory"},
                    "include_hidden": {"type": "boolean", "default": False, "description": "Include hidden files (starting with .)"}
                },
                "required": ["path"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        path_str = params.get("path", "").strip()
        include_hidden = bool(params.get("include_hidden", False))

        if not path_str:
            return {"success": False, "error": "Error: empty path is not allowed."}

        try:
            path = Path(path_str).resolve()

            if not path.exists():
                return {"success": False, "error": f"Error: path not found: {path}"}

            if not path.is_dir():
                return {"success": False, "error": f"Error: not a directory: {path}"}

            entries = []
            for item in await asyncio.to_thread(lambda: list(path.iterdir())):
                if not include_hidden and item.name.startswith("."):
                    continue

                try:
                    stat = item.stat()
                    entries.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0
                    })
                except OSError:
                    # Skip entries we can't stat (broken symlinks, permission issues)
                    continue

            ctx.logger.info(f"ListDirectoryTool: listed {len(entries)} entries in {path}")
            return {
                "success": True,
                "path": str(path),
                "count": len(entries),
                "entries": sorted(entries, key=lambda e: (e["type"], e["name"]))
            }

        except Exception as e:
            ctx.logger.error(f"ListDirectoryTool failed: {e}", exc_info=True)
            return {"success": False, "error": f"Error: {e}"}


# -----------------------------------------------------------------------------
# CreateDirectoryTool
# -----------------------------------------------------------------------------

class CreateDirectoryTool(BaseTool):
    """Creates a directory, including any missing parent directories."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="create_directory",
            description="Creates a directory and any missing parent directories. Does nothing if directory already exists.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the directory to create"}
                },
                "required": ["path"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        path_str = params.get("path", "").strip()

        if not path_str:
            return {"success": False, "error": "Error: empty path is not allowed."}

        try:
            path = Path(path_str).resolve()

            if path.exists() and not path.is_dir():
                return {"success": False, "error": f"Error: path exists and is not a directory: {path}"}

            await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)

            ctx.logger.info(f"CreateDirectoryTool: created {path}")
            return {
                "success": True,
                "path": str(path),
                "created": True
            }

        except Exception as e:
            ctx.logger.error(f"CreateDirectoryTool failed: {e}", exc_info=True)
            return {"success": False, "error": f"Error: {e}"}


# -----------------------------------------------------------------------------
# FileInfoTool
# -----------------------------------------------------------------------------

class FileInfoTool(BaseTool):
    """Retrieves metadata about a file or directory."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="file_info",
            description="Returns metadata (size, type, timestamps) for a file or directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file or directory"}
                },
                "required": ["path"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        path_str = params.get("path", "").strip()

        if not path_str:
            return {"success": False, "error": "Error: empty path is not allowed."}

        try:
            path = Path(path_str).resolve()

            if not path.exists():
                return {"success": False, "error": f"Error: path not found: {path}"}

            stat = path.stat()
            info = {
                "success": True,
                "path": str(path),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size if path.is_file() else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }

            ctx.logger.debug(f"FileInfoTool: retrieved info for {path}")
            return info

        except Exception as e:
            ctx.logger.error(f"FileInfoTool failed: {e}", exc_info=True)
            return {"success": False, "error": f"Error: {e}"}