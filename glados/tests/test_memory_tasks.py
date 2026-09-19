# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, AsyncMock

from glados.core.context import RuntimeContext
from glados.autonomous.tasks.memory_tasks import consolidate_memory


class TestMemoryTasks:
    @pytest.mark.asyncio
    async def test_consolidate_memory_calls_manager(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.consolidate = AsyncMock()
        
        await consolidate_memory(ctx)
        
        ctx.memory.consolidate.assert_called_once()

    @pytest.mark.asyncio
    async def test_consolidate_memory_handles_missing_memory(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = None
        
        # Must not raise an exception if memory subsystem is absent
        await consolidate_memory(ctx)