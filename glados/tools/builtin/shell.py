# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in Shell Execution Tool.
Provides safe, timeout-guarded shell command execution for the GLaDOS agent.
"""

import asyncio
from typing import Any

from glados.core.context import RuntimeContext
from glados.tools.base import BaseTool, ToolDefinition


class ShellTool(BaseTool):
    """
    Executes shell commands asynchronously with timeout protection.
    Returns structured output (stdout, stderr, returncode).
    
    SECURITY NOTE: This tool executes arbitrary shell commands.
    In production, access should be restricted via policy layer (Phase 7).
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="shell_exec",
            description=(
                "Executes a shell command and returns stdout, stderr, and exit code. "
                "Use with caution. Supports timeout to prevent hanging."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds.",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes a shell command asynchronously.
        
        :param ctx: Runtime context (used for logging).
        :param params: Dictionary with 'command' (str) and optional 'timeout' (int).
        :return: Dict with 'stdout', 'stderr', and 'returncode'.
        """
        command = params.get("command", "").strip()
        timeout = params.get("timeout", 30)

        if not command:
            ctx.logger.warning("ShellTool received empty command.")
            return {
                "stdout": "",
                "stderr": "Error: empty command is not allowed.",
                "returncode": -1
            }

        ctx.logger.info(f"ShellTool executing: {command} (timeout={timeout}s)")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            returncode = process.returncode or 0

            ctx.logger.debug(
                f"ShellTool completed: returncode={returncode}, "
                f"stdout_len={len(stdout)}, stderr_len={len(stderr)}"
            )

            return {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode
            }

        except asyncio.TimeoutError:
            # Kill the process if it exceeded the timeout
            try:
                process.kill()  # type: ignore[possibly-undefined]
                await process.wait()  # type: ignore[possibly-undefined]
            except ProcessLookupError:
                pass

            ctx.logger.warning(f"ShellTool command timed out after {timeout}s: {command}")
            return {
                "stdout": "",
                "stderr": f"Error: command timed out after {timeout} seconds.",
                "returncode": -1
            }

        except Exception as e:
            ctx.logger.error(f"ShellTool unexpected error: {e}", exc_info=True)
            return {
                "stdout": "",
                "stderr": f"Error: {str(e)}",
                "returncode": -1
            }