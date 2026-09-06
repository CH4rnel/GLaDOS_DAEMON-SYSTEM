# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS PythonExecTool.
Follows TDD methodology to define the contract for safe, isolated Python code execution.
"""

import asyncio
from typing import Any

import pytest

from glados.tools.builtin.python_exec import PythonExecTool
from glados.core.context import RuntimeContext


class MockRuntimeContext:
    """Minimal mock for RuntimeContext."""
    class MockLogger:
        def debug(self, *args: Any, **kwargs: Any) -> None: pass
        def info(self, *args: Any, **kwargs: Any) -> None: pass
        def warning(self, *args: Any, **kwargs: Any) -> None: pass
        def error(self, *args: Any, **kwargs: Any) -> None: pass

    logger = MockLogger()


class TestPythonExecToolDefinition:
    """Tests for PythonExecTool metadata."""

    def test_python_exec_tool_has_valid_definition(self):
        """Test that PythonExecTool provides a correct definition."""
        tool = PythonExecTool()
        defn = tool.definition

        assert defn.name == "python_exec"
        assert len(defn.description) > 0
        assert "code" in defn.parameters.get("properties", {})
        assert "timeout" in defn.parameters.get("properties", {})


class TestPythonExecToolExecution:
    """Tests for PythonExecTool async execution."""

    def test_execute_valid_simple_code(self):
        """Test executing a simple, valid Python script."""
        tool = PythonExecTool()
        ctx = MockRuntimeContext()
        code = "print('Hello, Omnissiah!')"

        result = asyncio.run(tool.execute(ctx, {"code": code, "timeout": 5}))

        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Hello, Omnissiah!" in result["stdout"]

    def test_execute_code_with_syntax_error(self):
        """Test executing code with a syntax error."""
        tool = PythonExecTool()
        ctx = MockRuntimeContext()
        code = "print('missing quote)"

        result = asyncio.run(tool.execute(ctx, {"code": code, "timeout": 5}))

        assert result["success"] is False
        assert "SyntaxError" in result["stderr"] or "error" in result["stderr"].lower()

    def test_execute_code_with_runtime_error(self):
        """Test executing code that raises a runtime exception."""
        tool = PythonExecTool()
        ctx = MockRuntimeContext()
        code = "raise ValueError('Intentional error')"

        result = asyncio.run(tool.execute(ctx, {"code": code, "timeout": 5}))

        assert result["success"] is False
        assert "ValueError" in result["stderr"]

    def test_execute_timeout_protection(self):
        """Test that long-running code is killed after timeout."""
        tool = PythonExecTool()
        ctx = MockRuntimeContext()
        code = "import time\ntime.sleep(10)"

        result = asyncio.run(tool.execute(ctx, {"code": code, "timeout": 1}))

        assert result["success"] is False
        assert "timeout" in result["error"].lower() or result["returncode"] != 0

    def test_execute_empty_code_rejected(self):
        """Test that empty code is rejected."""
        tool = PythonExecTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"code": "", "timeout": 5}))

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_execute_output_truncation(self):
        """Test that excessive output is truncated to prevent memory exhaustion."""
        tool = PythonExecTool()
        ctx = MockRuntimeContext()
        # Generate ~20KB of output
        code = "print('A' * 20000)"

        result = asyncio.run(tool.execute(ctx, {"code": code, "timeout": 5, "max_output_bytes": 10000}))

        assert result["success"] is True
        assert len(result["stdout"].encode("utf-8")) <= 10000
        assert "[OUTPUT TRUNCATED]" in result["stdout"]