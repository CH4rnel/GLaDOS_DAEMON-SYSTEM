# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in Python Execution Tool.
Provides isolated, timeout-guarded execution of Python code snippets.

Security Considerations:
- Executes in a separate subprocess to prevent main daemon state corruption.
- Uses asyncio.create_subprocess_exec (NO shell=True) to prevent shell injection.
- Strict timeout limits prevent infinite loops.
- Output truncation prevents memory exhaustion.
- WARNING: This tool can still execute arbitrary system commands via os/system modules. 
  A strict AST-based sandbox or seccomp policy is required for Phase 7 (Autonomous Mode).
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any

from glados.core.context import RuntimeContext
from glados.tools.base import BaseTool, ToolDefinition


class PythonExecTool(BaseTool):
    """
    Executes Python code snippets in an isolated subprocess.
    Returns structured output (stdout, stderr, returncode).
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="python_exec",
            description=(
                "Executes a Python code snippet in an isolated subprocess. "
                "Use with extreme caution. Supports timeout and output size limits."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds.",
                        "default": 10
                    },
                    "max_output_bytes": {
                        "type": "integer",
                        "description": "Maximum size of stdout/stderr in bytes before truncation.",
                        "default": 10240
                    }
                },
                "required": ["code"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes Python code asynchronously in a temporary file.
        
        :param ctx: Runtime context (used for logging).
        :param params: Dictionary with 'code' (str), 'timeout' (int), 'max_output_bytes' (int).
        :return: Dict with 'success', 'stdout', 'stderr', 'returncode', and optional 'error'.
        """
        code = params.get("code", "").strip()
        timeout = int(params.get("timeout", 10))
        max_output = int(params.get("max_output_bytes", 10240))

        if not code:
            return {"success": False, "error": "Error: 'code' is required and cannot be empty."}

        ctx.logger.info(f"PythonExecTool: executing code snippet (timeout={timeout}s, max_output={max_output}B)")

        # Create a temporary file for the code to avoid passing via command line args
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name

            ctx.logger.debug(f"PythonExecTool: wrote code to temporary file {tmp_path}")

            try:
                # SECURITY: create_subprocess_exec ensures 'python' is the only executable.
                process = await asyncio.create_subprocess_exec(
                    "python",
                    tmp_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")

                # Truncate output if it exceeds limits
                truncated = False
                if len(stdout.encode("utf-8")) > max_output:
                    stdout = stdout.encode("utf-8")[:max_output].decode("utf-8", errors="ignore") + "\n[OUTPUT TRUNCATED]"
                    truncated = True
                
                if len(stderr.encode("utf-8")) > max_output:
                    stderr = stderr.encode("utf-8")[:max_output].decode("utf-8", errors="ignore") + "\n[OUTPUT TRUNCATED]"
                    truncated = True

                returncode = process.returncode or 0

                if returncode == 0:
                    ctx.logger.debug(f"PythonExecTool completed successfully: returncode={returncode}")
                    return {
                        "success": True,
                        "stdout": stdout.strip(),
                        "stderr": stderr.strip(),
                        "returncode": returncode,
                        "truncated": truncated
                    }
                else:
                    ctx.logger.warning(f"PythonExecTool failed: returncode={returncode}, stderr={stderr[:100]}")
                    return {
                        "success": False,
                        "stdout": stdout.strip(),
                        "stderr": stderr.strip(),
                        "returncode": returncode,
                        "error": f"Python execution failed with code {returncode}"
                    }

            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                
                ctx.logger.warning(f"PythonExecTool timed out after {timeout}s")
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "",
                    "returncode": -1,
                    "error": f"Error: execution timed out after {timeout} seconds."
                }

        except FileNotFoundError:
            ctx.logger.error("PythonExecTool failed: 'python' executable not found in system PATH.")
            return {
                "success": False,
                "error": "Error: 'python' executable not found. Please ensure Python is installed."
            }
        except Exception as e:
            ctx.logger.error(f"PythonExecTool unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
        finally:
            # Cleanup temporary file
            try:
                Path(tmp_path).unlink(missing_ok=True)
                ctx.logger.debug(f"PythonExecTool: cleaned up temporary file {tmp_path}")
            except Exception as e:
                ctx.logger.warning(f"PythonExecTool: failed to cleanup temp file {tmp_path}: {e}")