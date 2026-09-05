# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS FileSystem tools.
Follows TDD methodology to define the contract for safe filesystem operations.
"""

import asyncio
from pathlib import Path
from typing import Any

import pytest

from glados.tools.builtin.filesystem import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    CreateDirectoryTool,
    FileInfoTool,
)
from glados.core.context import RuntimeContext


class MockRuntimeContext:
    """Minimal mock for RuntimeContext."""
    class MockLogger:
        def debug(self, *args: Any, **kwargs: Any) -> None: pass
        def info(self, *args: Any, **kwargs: Any) -> None: pass
        def warning(self, *args: Any, **kwargs: Any) -> None: pass
        def error(self, *args: Any, **kwargs: Any) -> None: pass

    logger = MockLogger()


# -----------------------------------------------------------------------------
# Tests for ReadFileTool
# -----------------------------------------------------------------------------

class TestReadFileTool:
    """Tests for reading files from the filesystem."""

    def test_read_existing_file(self, tmp_path: Path):
        """Test reading content of an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, Omnissiah!", encoding="utf-8")

        tool = ReadFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(test_file)}))

        assert result["success"] is True
        assert result["content"] == "Hello, Omnissiah!"
        assert result["size"] == len("Hello, Omnissiah!")

    def test_read_nonexistent_file(self, tmp_path: Path):
        """Test reading a file that does not exist."""
        tool = ReadFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path / "missing.txt")}))

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_read_file_too_large(self, tmp_path: Path):
        """Test that reading a file exceeding max_size is rejected."""
        large_file = tmp_path / "large.bin"
        large_file.write_bytes(b"x" * 2_000_000)  # 2MB

        tool = ReadFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "path": str(large_file),
            "max_size": 1_000_000  # 1MB limit
        }))

        assert result["success"] is False
        assert "too large" in result["error"].lower()

    def test_read_directory_as_file(self, tmp_path: Path):
        """Test that reading a directory is rejected."""
        tool = ReadFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path)}))

        assert result["success"] is False
        assert "not a file" in result["error"].lower()

    def test_read_empty_path_rejected(self):
        """Test that an empty path is rejected."""
        tool = ReadFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": ""}))

        assert result["success"] is False
        assert "empty" in result["error"].lower() or "invalid" in result["error"].lower()


# -----------------------------------------------------------------------------
# Tests for WriteFileTool
# -----------------------------------------------------------------------------

class TestWriteFileTool:
    """Tests for writing files to the filesystem."""

    def test_write_new_file(self, tmp_path: Path):
        """Test writing content to a new file."""
        target = tmp_path / "new_file.txt"

        tool = WriteFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "path": str(target),
            "content": "New content"
        }))

        assert result["success"] is True
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "New content"

    def test_write_overwrite_existing(self, tmp_path: Path):
        """Test overwriting an existing file."""
        target = tmp_path / "existing.txt"
        target.write_text("old", encoding="utf-8")

        tool = WriteFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "path": str(target),
            "content": "new"
        }))

        assert result["success"] is True
        assert target.read_text(encoding="utf-8") == "new"

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        """Test that writing creates missing parent directories."""
        target = tmp_path / "sub" / "dir" / "file.txt"

        tool = WriteFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "path": str(target),
            "content": "nested"
        }))

        assert result["success"] is True
        assert target.exists()

    def test_write_empty_path_rejected(self):
        """Test that an empty path is rejected."""
        tool = WriteFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": "", "content": "x"}))

        assert result["success"] is False

    def test_write_empty_content_allowed(self, tmp_path: Path):
        """Test that writing empty content is allowed (creates empty file)."""
        target = tmp_path / "empty.txt"

        tool = WriteFileTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {
            "path": str(target),
            "content": ""
        }))

        assert result["success"] is True
        assert target.read_text(encoding="utf-8") == ""


# -----------------------------------------------------------------------------
# Tests for ListDirectoryTool
# -----------------------------------------------------------------------------

class TestListDirectoryTool:
    """Tests for listing directory contents."""

    def test_list_empty_directory(self, tmp_path: Path):
        """Test listing an empty directory."""
        tool = ListDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path)}))

        assert result["success"] is True
        assert result["entries"] == []

    def test_list_directory_with_files(self, tmp_path: Path):
        """Test listing a directory with files and subdirectories."""
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.txt").write_text("b")
        (tmp_path / "subdir").mkdir()

        tool = ListDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path)}))

        assert result["success"] is True
        names = {e["name"] for e in result["entries"]}
        assert names == {"file1.txt", "file2.txt", "subdir"}

        # Check types
        types = {e["name"]: e["type"] for e in result["entries"]}
        assert types["subdir"] == "directory"
        assert types["file1.txt"] == "file"

    def test_list_nonexistent_directory(self, tmp_path: Path):
        """Test listing a non-existent directory."""
        tool = ListDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path / "missing")}))

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "not a directory" in result["error"].lower()

    def test_list_file_as_directory(self, tmp_path: Path):
        """Test that listing a file (not directory) is rejected."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")

        tool = ListDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(file_path)}))

        assert result["success"] is False
        assert "not a directory" in result["error"].lower()


# -----------------------------------------------------------------------------
# Tests for CreateDirectoryTool
# -----------------------------------------------------------------------------

class TestCreateDirectoryTool:
    """Tests for creating directories."""

    def test_create_new_directory(self, tmp_path: Path):
        """Test creating a new directory."""
        target = tmp_path / "new_dir"

        tool = CreateDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(target)}))

        assert result["success"] is True
        assert target.is_dir()

    def test_create_nested_directories(self, tmp_path: Path):
        """Test creating nested directories."""
        target = tmp_path / "a" / "b" / "c"

        tool = CreateDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(target)}))

        assert result["success"] is True
        assert target.is_dir()

    def test_create_existing_directory_ok(self, tmp_path: Path):
        """Test that creating an existing directory does not fail."""
        existing = tmp_path / "existing"
        existing.mkdir()

        tool = CreateDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(existing)}))

        assert result["success"] is True

    def test_create_directory_on_file_fails(self, tmp_path: Path):
        """Test that creating a directory where a file exists fails."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")

        tool = CreateDirectoryTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(file_path)}))

        assert result["success"] is False


# -----------------------------------------------------------------------------
# Tests for FileInfoTool
# -----------------------------------------------------------------------------

class TestFileInfoTool:
    """Tests for retrieving file metadata."""

    def test_file_info_for_file(self, tmp_path: Path):
        """Test getting info about a file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("hello")

        tool = FileInfoTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(file_path)}))

        assert result["success"] is True
        assert result["type"] == "file"
        assert result["size"] == 5
        assert "modified" in result
        assert "created" in result

    def test_file_info_for_directory(self, tmp_path: Path):
        """Test getting info about a directory."""
        tool = FileInfoTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path)}))

        assert result["success"] is True
        assert result["type"] == "directory"

    def test_file_info_nonexistent(self, tmp_path: Path):
        """Test getting info about a non-existent path."""
        tool = FileInfoTool()
        ctx = MockRuntimeContext()

        result = asyncio.run(tool.execute(ctx, {"path": str(tmp_path / "missing")}))

        assert result["success"] is False
        assert "not found" in result["error"].lower()