# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS GitTool.
Follows TDD methodology to define the contract for safe git command execution.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Any

import pytest

from glados.tools.builtin.git import GitTool
from glados.core.context import RuntimeContext


class MockRuntimeContext:
    """Minimal mock for RuntimeContext."""
    class MockLogger:
        def debug(self, *args: Any, **kwargs: Any) -> None: pass
        def info(self, *args: Any, **kwargs: Any) -> None: pass
        def warning(self, *args: Any, **kwargs: Any) -> None: pass
        def error(self, *args: Any, **kwargs: Any) -> None: pass

    logger = MockLogger()


def run_git_init(repo_path: Path) -> None:
    """Helper to initialize a git repo for testing."""
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@glados.local"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "GLaDOS Test"], cwd=repo_path, check=True, capture_output=True)


class TestGitToolDefinition:
    """Tests for GitTool metadata."""

    def test_git_tool_has_valid_definition(self):
        """Test that GitTool provides a correct definition."""
        tool = GitTool()
        defn = tool.definition

        assert defn.name == "git_exec"
        assert len(defn.description) > 0
        assert "cwd" in defn.parameters.get("properties", {})
        assert "args" in defn.parameters.get("properties", {})


class TestGitToolExecution:
    """Tests for GitTool async execution."""

    def test_git_status_in_valid_repo(self, tmp_path: Path):
        """Test executing git status in a valid repository."""
        run_git_init(tmp_path)
        (tmp_path / "test.txt").write_text("hello")

        tool = GitTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "cwd": str(tmp_path),
            "args": ["status", "--porcelain"]
        }))

        assert result["success"] is True
        assert result["returncode"] == 0
        assert "test.txt" in result["stdout"]

    def test_git_status_not_in_repo(self, tmp_path: Path):
        """Test executing git command outside a repository."""
        tool = GitTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "cwd": str(tmp_path),
            "args": ["status"]
        }))

        assert result["success"] is False
        assert "not a git repository" in result["stderr"].lower() or result["returncode"] != 0

    def test_git_commit_in_valid_repo(self, tmp_path: Path):
        """Test executing git commit in a valid repository."""
        run_git_init(tmp_path)
        test_file = tmp_path / "commit_test.txt"
        test_file.write_text("content")
        
        # Stage the file first
        subprocess.run(["git", "add", "commit_test.txt"], cwd=tmp_path, check=True, capture_output=True)

        tool = GitTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "cwd": str(tmp_path),
            "args": ["commit", "-m", "Test commit by GLaDOS"]
        }))

        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Test commit by GLaDOS" in result["stdout"]

    def test_git_log_in_valid_repo(self, tmp_path: Path):
        """Test executing git log to retrieve history."""
        run_git_init(tmp_path)
        test_file = tmp_path / "log_test.txt"
        test_file.write_text("content")
        subprocess.run(["git", "add", "log_test.txt"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True)

        tool = GitTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "cwd": str(tmp_path),
            "args": ["log", "--oneline", "-n", "1"]
        }))

        assert result["success"] is True
        assert result["returncode"] == 0
        assert "Initial commit" in result["stdout"]

    def test_git_invalid_cwd_rejected(self):
        """Test that a non-existent directory is rejected."""
        tool = GitTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "cwd": "/nonexistent/path/xyz",
            "args": ["status"]
        }))

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "no such file" in result["error"].lower()

    def test_git_empty_args_rejected(self):
        """Test that empty args list is rejected."""
        tool = GitTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "cwd": "/tmp",
            "args": []
        }))

        assert result["success"] is False
        assert "empty" in result["error"].lower()