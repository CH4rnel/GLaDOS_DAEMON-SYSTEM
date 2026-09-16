# glados/tools/builtin/shell.py
# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in Shell Execution Tool.
Provides safe, timeout-guarded shell command execution for the GLaDOS agent.

SECURITY NOTE (formerly a TODO, now implemented — see glados/security/policy.py):
When a SecurityPolicy is attached to RuntimeContext, this tool enforces a
binary allowlist and, by default (`shell_safe_mode=True`), executes via
`create_subprocess_exec` on a `shlex`-parsed argv instead of
`create_subprocess_shell`. That removes shell metacharacter interpretation
entirely (no `;`, `|`, `&&`, backticks, redirection) — an LLM-controlled
command string can no longer inject a second command. Multi-stage shell
pipelines will stop working in this mode; if you genuinely need them, set
`shell_safe_mode: false` in configs/security.yaml, which keeps the binary
allowlist but restores raw shell interpretation for the *first* token only
(the rest of the string is still shell-parsed, so only do this if you trust
every caller of this tool, not just the top-level binary).
"""

import asyncio
import shlex
from typing import Any

from glados.core.context import RuntimeContext
from glados.security.policy import PolicyViolation, get_policy, log_missing_policy
from glados.tools.base import BaseTool, ToolDefinition


class ShellTool(BaseTool):
    """
    Executes shell commands asynchronously with timeout protection.
    Returns structured output (stdout, stderr, returncode).
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

        policy = get_policy(ctx)
        safe_mode = True
        if policy is None:
            log_missing_policy("ShellTool")
        else:
            try:
                argv = shlex.split(command)
                policy.check_shell_command(argv)
            except (ValueError, PolicyViolation) as e:
                ctx.logger.warning(f"ShellTool denied by policy: {e}")
                return {
                    "stdout": "",
                    "stderr": f"Error: denied by security policy: {e}",
                    "returncode": -1
                }
            safe_mode = policy.shell_safe_mode
            timeout = min(timeout, policy.max_shell_timeout)

        ctx.logger.info(f"ShellTool executing: {command} (timeout={timeout}s, safe_mode={safe_mode})")

        try:
            if policy is not None and safe_mode:
                # No shell interpretation at all — argv is executed directly.
                argv = shlex.split(command)
                process = await asyncio.create_subprocess_exec(
                    *argv,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
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