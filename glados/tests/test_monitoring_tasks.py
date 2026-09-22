# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from glados.core.context import RuntimeContext
from glados.autonomous.tasks.monitoring_tasks import monitor_system_resources


class TestMonitoringTasks:
    @pytest.mark.asyncio
    async def test_monitor_collects_and_saves_metrics(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.add_short_term_record = MagicMock()
        
        with patch("glados.autonomous.tasks.monitoring_tasks.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 45.2
            mock_psutil.virtual_memory.return_value = MagicMock(percent=67.8)
            mock_psutil.disk_usage.return_value = MagicMock(percent=82.1)
            
            await monitor_system_resources(ctx)
            
            ctx.memory.add_short_term_record.assert_called_once()
            call_args = ctx.memory.add_short_term_record.call_args
            assert call_args[0][0] == "system"
            assert "CPU: 45.2%" in call_args[0][1]
            assert "RAM: 67.8%" in call_args[0][1]
            assert "Disk: 82.1%" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_monitor_handles_missing_memory(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = None
        
        with patch("glados.autonomous.tasks.monitoring_tasks.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 10.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=20.0)
            mock_psutil.disk_usage.return_value = MagicMock(percent=30.0)
            
            # Must not raise an exception if memory subsystem is absent
            await monitor_system_resources(ctx)

    @pytest.mark.asyncio
    async def test_monitor_handles_psutil_failure(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        
        with patch("glados.autonomous.tasks.monitoring_tasks.psutil") as mock_psutil:
            mock_psutil.cpu_percent.side_effect = RuntimeError("Simulated psutil failure")
            
            # Must not raise an exception if psutil fails
            await monitor_system_resources(ctx)
            
            # Memory should not be called if collection failed
            ctx.memory.add_short_term_record.assert_not_called()