# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from glados.core.context import RuntimeContext
from glados.security import SecurityPolicy, PolicyViolation
from glados.tools.builtin.git import GitTool


class TestGitTool:
    def setup_method(self) -> None:
        self.mock_ctx = MagicMock(spec=RuntimeContext)
        self.mock_ctx.security = MagicMock(spec=SecurityPolicy)
        
        # Mock the resolved path to exist and be a directory
        self.mock_cwd = MagicMock(spec=Path)
        self.mock_cwd.exists.return_value = True
        self.mock_cwd.is_dir.return_value = True
        
        self.mock_ctx.security.resolve_within_fs_roots.return_value = self.mock_cwd
        self.mock_ctx.security.check_git_args.return_value = None
        self.mock_ctx.logger = MagicMock()
        self.tool = GitTool()

    def test_tool_initialization(self) -> None:
        assert self.tool is not None
        assert self.tool.definition.name == "git_exec"
        assert "git" in self.tool.definition.description.lower()

    @pytest.mark.asyncio
    async def test_execute_allowed_git_command_successfully(self) -> None:
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"On branch main\n", b""))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await self.tool.execute(
                self.mock_ctx, 
                {"cwd": "/safe/repo", "args": ["status"]}
            )

            assert result.get("success") is True
            assert "On branch main" in result.get("stdout", "")
            self.mock_ctx.security.check_git_args.assert_called_once_with(["status"])

    @pytest.mark.asyncio
    async def test_execute_blocks_disallowed_subcommand(self) -> None:
        self.mock_ctx.security.check_git_args.side_effect = PolicyViolation("subcommand 'push' is not allowed")

        result = await self.tool.execute(
            self.mock_ctx, 
            {"cwd": "/safe/repo", "args": ["push", "origin", "main"]}
        )

        assert result.get("success") is False
        assert "denied by security policy" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_execute_blocks_unallowed_remote_domain(self) -> None:
        self.mock_ctx.security.check_git_args.side_effect = PolicyViolation("remote does not match allowed domains")

        result = await self.tool.execute(
            self.mock_ctx, 
            {"cwd": "/safe/repo", "args": ["clone", "https://evil.com/malware.git"]}
        )

        assert result.get("success") is False
        assert "denied by security policy" in result.get("error", "").lower()
        
    @pytest.mark.asyncio
    async def test_execute_handles_missing_cwd(self) -> None:
        result = await self.tool.execute(
            self.mock_ctx, 
            {"args": ["status"]}
        )
        assert result.get("success") is False
        assert "'cwd' is required" in result.get("error", "")