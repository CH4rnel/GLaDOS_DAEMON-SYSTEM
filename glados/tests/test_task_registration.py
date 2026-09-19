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
        assert len(tasks) > 0

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