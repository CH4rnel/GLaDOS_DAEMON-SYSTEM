# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from glados.core.context import RuntimeContext
from glados.security import SecurityPolicy, PolicyViolation
from glados.tools.builtin.python_exec import PythonExecTool


class TestPythonExecTool:
    def setup_method(self) -> None:
        self.mock_ctx = MagicMock(spec=RuntimeContext)
        self.mock_ctx.security = MagicMock(spec=SecurityPolicy)
        self.mock_ctx.security.python_exec_enabled = True
        self.mock_ctx.logger = MagicMock()
        self.tool = PythonExecTool()

    def test_tool_initialization(self) -> None:
        assert self.tool is not None
        assert self.tool.definition.name == "python_exec"
        assert "python" in self.tool.definition.description.lower()

    @pytest.mark.asyncio
    async def test_execute_allowed_python_code_successfully(self) -> None:
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"Hello World\n", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await self.tool.execute(
                self.mock_ctx, 
                {"code": "print('Hello World')", "timeout": 5}
            )

            assert result.get("success") is True
            assert "Hello World" in result.get("stdout", "")
            assert result.get("returncode") == 0

    @pytest.mark.asyncio
    async def test_execute_blocks_when_disabled_by_policy(self) -> None:
        self.mock_ctx.security.check_python_exec.side_effect = PolicyViolation("python_exec is disabled by policy")

        result = await self.tool.execute(
            self.mock_ctx, 
            {"code": "print('test')"}
        )

        assert result.get("success") is False
        assert "denied by security policy" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_execute_handles_missing_code(self) -> None:
        result = await self.tool.execute(
            self.mock_ctx, 
            {"timeout": 5}
        )
        assert result.get("success") is False
        assert "'code' is required" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_execute_handles_timeout(self) -> None:
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process

            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                result = await self.tool.execute(
                    self.mock_ctx, 
                    {"code": "import time; time.sleep(20)", "timeout": 1}
                )

                assert result.get("success") is False
                assert "timed out" in result.get("error", "").lower()
                mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_truncates_large_output(self) -> None:
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            large_output = b"A" * 20000
            mock_process.communicate = AsyncMock(return_value=(large_output, b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await self.tool.execute(
                self.mock_ctx, 
                {"code": "print('A'*20000)", "max_output_bytes": 100}
            )

            assert result.get("success") is True
            assert result.get("truncated") is True
            assert len(result.get("stdout", "").encode("utf-8")) <= 100
            assert "[OUTPUT TRUNCATED]" in result.get("stdout", "")