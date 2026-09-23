# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from glados.core.context import RuntimeContext
from glados.security import SecurityPolicy, PolicyViolation
from glados.tools.builtin.filesystem import ReadFileTool, ListDirectoryTool


class TestFilesystemTools:
    def setup_method(self) -> None:
        self.mock_ctx = MagicMock(spec=RuntimeContext)
        self.mock_ctx.security = MagicMock(spec=SecurityPolicy)
        self.mock_ctx.logger = MagicMock()
        
        self.read_tool = ReadFileTool()
        self.list_tool = ListDirectoryTool()

    def test_read_file_tool_initialization(self) -> None:
        assert self.read_tool is not None
        assert self.read_tool.definition.name == "read_file"
        assert "read" in self.read_tool.definition.description.lower()

    @pytest.mark.asyncio
    async def test_read_file_success(self) -> None:
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.stat.return_value.st_size = 100
        
        with patch("glados.tools.builtin.filesystem._resolve_guarded", return_value=mock_path):
            with patch("asyncio.to_thread", return_value="mock file content") as mock_to_thread:
                result = await self.read_tool.execute(
                    self.mock_ctx, 
                    {"path": "/safe/path/test.txt"}
                )
                
                mock_to_thread.assert_called_once()
                assert result.get("success") is True
                assert result.get("content") == "mock file content"

    @pytest.mark.asyncio
    async def test_read_file_blocks_path_traversal(self) -> None:
        with patch("glados.tools.builtin.filesystem._resolve_guarded") as mock_resolve:
            mock_resolve.side_effect = PolicyViolation("outside roots")
            
            result = await self.read_tool.execute(
                self.mock_ctx, 
                {"path": "/etc/passwd"}
            )
            assert result.get("success") is False
            assert "error" in result
            assert "outside roots" in result["error"]

    def test_list_directory_tool_initialization(self) -> None:
        assert self.list_tool is not None
        assert self.list_tool.definition.name == "list_directory"

    @pytest.mark.asyncio
    async def test_list_directory_success(self) -> None:
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        
        mock_entry = MagicMock()
        mock_entry.name = "test.txt"
        mock_entry.is_dir.return_value = False
        mock_entry.stat.return_value.st_size = 50
        
        with patch("glados.tools.builtin.filesystem._resolve_guarded", return_value=mock_path):
            with patch("asyncio.to_thread", return_value=[mock_entry]):
                result = await self.list_tool.execute(
                    self.mock_ctx, 
                    {"path": "/safe/path/dir"}
                )
                
                assert result.get("success") is True
                assert result.get("count") == 1
                assert result["entries"][0]["name"] == "test.txt"