# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in Git Tool.
Provides safe, sandboxed git command execution for the GLaDOS agent.

Security:
- Uses asyncio.create_subprocess_exec (NOT shell=True) to prevent shell injection.
- The executable is strictly bound to "git".
- Working directory (cwd) is validated before execution.
"""

import asyncio
from pathlib import Path
from typing import Any

from glados.core.context import RuntimeContext
from glados.tools.base import BaseTool, ToolDefinition


class GitTool(BaseTool):
    """
    Executes git commands asynchronously in a specified directory.
    Returns structured output (stdout, stderr, returncode).
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="git_exec",
            description=(
                "Executes a git command in a specified directory. "
                "Use args as a list of strings, e.g., ['status', '--porcelain'] or ['commit', '-m', 'msg']. "
                "Safe from shell injection."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "cwd": {
                        "type": "string",
                        "description": "Absolute or relative path to the git repository working directory."
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of git subcommand and arguments (e.g., ['log', '--oneline', '-n', '5'])."
                    }
                },
                "required": ["cwd", "args"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes a git command asynchronously.
        
        :param ctx: Runtime context (used for logging).
        :param params: Dictionary with 'cwd' (str) and 'args' (list of str).
        :return: Dict with 'success', 'stdout', 'stderr', 'returncode', and optional 'error'.
        """
        cwd_str = params.get("cwd", "").strip()
        args = params.get("args", [])

        if not cwd_str:
            return {"success": False, "error": "Error: 'cwd' is required and cannot be empty."}
        
        if not isinstance(args, list) or len(args) == 0:
            return {"success": False, "error": "Error: 'args' must be a non-empty list of strings."}

        cwd_path = Path(cwd_str).resolve()

        if not cwd_path.exists() or not cwd_path.is_dir():
            return {"success": False, "error": f"Error: working directory not found: {cwd_path}"}

        command_str = f"git {' '.join(args)}"
        ctx.logger.info(f"GitTool executing: {command_str} in {cwd_path}")

        try:
            # SECURITY: create_subprocess_exec ensures 'git' is the only executable.
            # No shell=True, preventing any shell injection attacks.
            process = await asyncio.create_subprocess_exec(
                "git",
                *args,
                cwd=str(cwd_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"GIT_TERMINAL_PROMPT": "0"}  # Prevent git from hanging on password prompts
            )

            stdout_bytes, stderr_bytes = await process.communicate()

            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            returncode = process.returncode or 0

            if returncode == 0:
                ctx.logger.debug(f"GitTool completed successfully: returncode={returncode}")
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": returncode
                }
            else:
                ctx.logger.warning(f"GitTool failed: returncode={returncode}, stderr={stderr}")
                return {
                    "success": False,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": returncode,
                    "error": f"Git command failed with code {returncode}"
                }

        except FileNotFoundError:
            ctx.logger.error("GitTool failed: 'git' executable not found in system PATH.")
            return {
                "success": False,
                "error": "Error: 'git' executable not found. Please ensure git is installed."
            }
        except Exception as e:
            ctx.logger.error(f"GitTool unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }