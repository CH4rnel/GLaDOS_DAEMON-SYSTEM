# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from glados.core.context import RuntimeContext
from glados.autonomous.tasks.log_rotation_tasks import rotate_logs


class TestLogRotationTasks:
    @pytest.mark.asyncio
    async def test_rotate_logs_when_exceeds_threshold(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        
        with patch("glados.autonomous.tasks.log_rotation_tasks.Path") as mock_path:
            mock_log_file = MagicMock()
            mock_log_file.exists.return_value = True
            mock_log_file.stat.return_value.st_size = 15_000_000  # 15 MB
            mock_path.return_value = mock_log_file
            
            await rotate_logs(ctx, max_size_bytes=10_000_000)
            
            mock_log_file.rename.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_rotation_when_below_threshold(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        
        with patch("glados.autonomous.tasks.log_rotation_tasks.Path") as mock_path:
            mock_log_file = MagicMock()
            mock_log_file.exists.return_value = True
            mock_log_file.stat.return_value.st_size = 5_000_000  # 5 MB
            mock_path.return_value = mock_log_file
            
            await rotate_logs(ctx, max_size_bytes=10_000_000)
            
            mock_log_file.rename.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_missing_log_file(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        
        with patch("glados.autonomous.tasks.log_rotation_tasks.Path") as mock_path:
            mock_log_file = MagicMock()
            mock_log_file.exists.return_value = False
            mock_path.return_value = mock_log_file
            
            # Must not raise an exception if log file doesn't exist
            await rotate_logs(ctx, max_size_bytes=10_000_000)