# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from glados.core.context import RuntimeContext
from glados.security import SecurityPolicy, PolicyViolation
from glados.tools.builtin.shell import ShellTool


class TestShellTool:
    def setup_method(self) -> None:
        self.mock_ctx = MagicMock(spec=RuntimeContext)
        self.mock_ctx.security = MagicMock(spec=SecurityPolicy)
        self.mock_ctx.security.shell_safe_mode = True
        self.mock_ctx.security.max_shell_timeout = 60
        self.mock_ctx.security.check_shell_command.return_value = None
        self.mock_ctx.logger = MagicMock()
        self.tool = ShellTool()

    def test_tool_initialization(self) -> None:
        assert self.tool is not None
        assert self.tool.definition.name == "shell_exec"
        assert "shell" in self.tool.definition.description.lower()

    @pytest.mark.asyncio
    async def test_execute_allowed_command_successfully(self) -> None:
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"output data", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await self.tool.execute(
                self.mock_ctx, 
                {"command": "git status", "timeout": 10}
            )

            assert result["returncode"] == 0
            assert "output data" in result["stdout"]
            self.mock_ctx.security.check_shell_command.assert_called_once_with(["git", "status"])

    @pytest.mark.asyncio
    async def test_execute_blocks_disallowed_command(self) -> None:
        self.mock_ctx.security.check_shell_command.side_effect = PolicyViolation("binary 'rm' is not allowed")

        result = await self.tool.execute(
            self.mock_ctx, 
            {"command": "rm -rf /", "timeout": 10}
        )

        assert result["returncode"] == -1
        assert "denied by security policy" in result["stderr"].lower()

    @pytest.mark.asyncio
    async def test_execute_handles_missing_security_policy_gracefully(self) -> None:
        self.mock_ctx.security = None

        with patch("asyncio.create_subprocess_shell") as mock_exec_shell:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"fallback output", b""))
            mock_process.returncode = 0
            mock_exec_shell.return_value = mock_process

            with patch("glados.tools.builtin.shell.log_missing_policy") as mock_log_missing:
                result = await self.tool.execute(
                    self.mock_ctx, 
                    {"command": "echo test", "timeout": 10}
                )

                assert result["returncode"] == 0
                assert "fallback output" in result["stdout"]
                mock_log_missing.assert_called_once_with("ShellTool")