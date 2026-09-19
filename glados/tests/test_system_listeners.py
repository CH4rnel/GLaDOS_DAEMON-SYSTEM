# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock

from glados.core.context import RuntimeContext
from glados.core.event import Event, EventPriority
from glados.autonomous.listeners.system_listeners import create_system_boot_listener


class TestSystemListeners:
    @pytest.mark.asyncio
    async def test_boot_listener_updates_memory(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.add_short_term_record = MagicMock()
        
        listener = create_system_boot_listener(ctx)
        event = Event(
            type="system.boot", 
            priority=EventPriority.CRITICAL, 
            payload={"status": "online"}
        )
        
        await listener(event)
        
        ctx.memory.add_short_term_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_boot_listener_handles_missing_memory(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = None
        
        listener = create_system_boot_listener(ctx)
        event = Event(type="system.boot", payload={})
        
        # Must not raise an exception if memory subsystem is absent
        await listener(event)