# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from glados.core.context import RuntimeContext
from glados.autonomous.events import EventHandler
from glados.autonomous.tasks.registration import create_default_tasks


class TestTaskRegistration:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.event_handler = MagicMock(spec=EventHandler)

    def test_create_default_tasks_returns_list(self) -> None:
        tasks = create_default_tasks(self.ctx, self.event_handler)
        
        assert isinstance(tasks, list)
        assert len(tasks) >= 4

    def test_memory_consolidation_task_configuration(self) -> None:
        tasks = create_default_tasks(self.ctx, self.event_handler)
        
        consolidation_task = next((t for t in tasks if t.id == "memory_consolidation"), None)
        assert consolidation_task is not None
        assert consolidation_task.name == "Memory Consolidation"
        assert consolidation_task.cron_expression == "*/5 * * * *"

    @pytest.mark.asyncio
    async def test_memory_consolidation_callback_execution(self) -> None:
        self.ctx.memory = MagicMock()
        self.ctx.memory.consolidate = AsyncMock()
        
        tasks = create_default_tasks(self.ctx, self.event_handler)
        consolidation_task = next(t for t in tasks if t.id == "memory_consolidation")
        
        await consolidation_task.callback()
        
        self.ctx.memory.consolidate.assert_called_once()

    def test_system_monitoring_task_configuration(self) -> None:
        tasks = create_default_tasks(self.ctx, self.event_handler)
        
        monitoring_task = next((t for t in tasks if t.id == "system_monitoring"), None)
        assert monitoring_task is not None
        assert monitoring_task.name == "System Resource Monitoring"
        assert monitoring_task.cron_expression == "*/2 * * * *"

    @pytest.mark.asyncio
    async def test_system_monitoring_callback_execution(self) -> None:
        self.ctx.memory = MagicMock()
        self.ctx.memory.add_short_term_record = MagicMock()
        
        tasks = create_default_tasks(self.ctx, self.event_handler)
        monitoring_task = next(t for t in tasks if t.id == "system_monitoring")
        
        with patch("glados.autonomous.tasks.monitoring_tasks.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0)
            mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)
            
            await monitoring_task.callback()
            
            self.ctx.memory.add_short_term_record.assert_called_once()

    def test_log_rotation_task_configuration(self) -> None:
        tasks = create_default_tasks(self.ctx, self.event_handler)
        
        rotation_task = next((t for t in tasks if t.id == "log_rotation"), None)
        assert rotation_task is not None
        assert rotation_task.name == "Log Rotation"
        assert rotation_task.cron_expression == "0 * * * *"

    @pytest.mark.asyncio
    async def test_log_rotation_callback_execution(self) -> None:
        tasks = create_default_tasks(self.ctx, self.event_handler)
        rotation_task = next(t for t in tasks if t.id == "log_rotation")
        
        with patch("glados.autonomous.tasks.log_rotation_tasks.Path") as mock_path:
            mock_log_file = MagicMock()
            mock_log_file.exists.return_value = True
            mock_log_file.stat.return_value.st_size = 5_000_000
            mock_path.return_value = mock_log_file
            
            await rotation_task.callback()

    def test_system_diagnostics_task_configuration(self) -> None:
        tasks = create_default_tasks(self.ctx, self.event_handler)
        
        diagnostics_task = next((t for t in tasks if t.id == "system_diagnostics"), None)
        assert diagnostics_task is not None
        assert diagnostics_task.name == "System Self-Diagnostics"
        assert diagnostics_task.cron_expression == "*/10 * * * *"

    @pytest.mark.asyncio
    async def test_system_diagnostics_callback_execution(self) -> None:
        self.ctx.memory = MagicMock()
        self.ctx.memory.add_short_term_record = MagicMock()
        self.ctx.llm_registry = MagicMock()
        self.ctx.tools = MagicMock()
        
        tasks = create_default_tasks(self.ctx, self.event_handler)
        diagnostics_task = next(t for t in tasks if t.id == "system_diagnostics")
        
        await diagnostics_task.callback()
        
        self.ctx.memory.add_short_term_record.assert_called_once()