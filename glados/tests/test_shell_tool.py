# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS ShellTool.
Follows TDD methodology to define the contract for safe shell command execution.
"""

import asyncio
from typing import Any

import pytest

from glados.tools.builtin.shell import ShellTool
from glados.core.context import RuntimeContext


class MockRuntimeContext:
    """Minimal mock for RuntimeContext."""
    class MockLogger:
        def debug(self, *args: Any, **kwargs: Any) -> None: pass
        def info(self, *args: Any, **kwargs: Any) -> None: pass
        def warning(self, *args: Any, **kwargs: Any) -> None: pass
        def error(self, *args: Any, **kwargs: Any) -> None: pass

    logger = MockLogger()


class TestShellToolDefinition:
    """Tests for ShellTool metadata."""

    def test_shell_tool_has_valid_definition(self):
        """Test that ShellTool provides a correct definition."""
        tool = ShellTool()
        defn = tool.definition

        assert defn.name == "shell_exec"
        assert len(defn.description) > 0
        assert "command" in defn.parameters.get("properties", {})


class TestShellToolExecution:
    """Tests for ShellTool async execution."""

    def test_execute_simple_command(self):
        """Test executing a simple echo command."""
        tool = ShellTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"command": "echo hello"}))

        assert result["returncode"] == 0
        assert "hello" in result["stdout"]
        assert result["stderr"] == ""

    def test_execute_command_with_error(self):
        """Test executing a command that returns a non-zero exit code."""
        tool = ShellTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"command": "ls /nonexistent_path_xyz"}))

        assert result["returncode"] != 0
        assert len(result["stderr"]) > 0

    def test_execute_command_timeout(self):
        """Test that a long-running command is killed after timeout."""
        tool = ShellTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "command": "sleep 10",
            "timeout": 1
        }))

        assert result["returncode"] != 0
        assert "timed out" in result["stderr"].lower() or result["returncode"] == -1

    def test_execute_empty_command_rejected(self):
        """Test that an empty command is rejected."""
        tool = ShellTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"command": ""}))

        assert result["returncode"] != 0
        assert "empty" in result["stderr"].lower() or "invalid" in result["stderr"].lower()

    def test_execute_returns_structured_result(self):
        """Test that the result always contains stdout, stderr, and returncode."""
        tool = ShellTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"command": "echo test"}))

        assert "stdout" in result
        assert "stderr" in result
        assert "returncode" in result