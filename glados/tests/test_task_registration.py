# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from glados.core.context import RuntimeContext
from glados.autonomous.tasks.registration import create_default_tasks


class TestTaskRegistration:
    def test_create_default_tasks_returns_list(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        tasks = create_default_tasks(ctx)
        
        assert isinstance(tasks, list)
        assert len(tasks) >= 2

    def test_memory_consolidation_task_configuration(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        tasks = create_default_tasks(ctx)
        
        consolidation_task = next((t for t in tasks if t.id == "memory_consolidation"), None)
        assert consolidation_task is not None
        assert consolidation_task.name == "Memory Consolidation"
        assert consolidation_task.cron_expression == "*/5 * * * *"

    @pytest.mark.asyncio
    async def test_memory_consolidation_callback_execution(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.consolidate = AsyncMock()
        
        tasks = create_default_tasks(ctx)
        consolidation_task = next(t for t in tasks if t.id == "memory_consolidation")
        
        # Execute the wrapped callback
        await consolidation_task.callback()
        
        ctx.memory.consolidate.assert_called_once()

    def test_system_monitoring_task_configuration(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        tasks = create_default_tasks(ctx)
        
        monitoring_task = next((t for t in tasks if t.id == "system_monitoring"), None)
        assert monitoring_task is not None
        assert monitoring_task.name == "System Resource Monitoring"
        assert monitoring_task.cron_expression == "*/2 * * * *"

    @pytest.mark.asyncio
    async def test_system_monitoring_callback_execution(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.add_short_term_record = MagicMock()
        
        tasks = create_default_tasks(ctx)
        monitoring_task = next(t for t in tasks if t.id == "system_monitoring")
        
        with patch("glados.autonomous.tasks.monitoring_tasks.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
            mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)
            
            # Execute the wrapped callback
            await monitoring_task.callback()
            
            ctx.memory.add_short_term_record.assert_called_once()