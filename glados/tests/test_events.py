# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
import asyncio
from unittest.mock import MagicMock

from glados.core.context import RuntimeContext
from glados.core.event import Event, EventPriority
from glados.autonomous.events import EventHandler


class TestAsyncEventHandler:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.handler = EventHandler(ctx=self.ctx)

    @pytest.mark.asyncio
    async def test_subscribe_and_process(self) -> None:
        received_types = []
        
        def callback(event: Event) -> None:
            received_types.append(event.type)

        self.handler.subscribe("system.boot", callback)
        self.handler.publish(Event(type="system.boot", payload={"status": "ok"}))

        await self.handler.process_pending_events()

        assert len(received_types) == 1
        assert received_types[0] == "system.boot"
        assert not self.handler._queue

    @pytest.mark.asyncio
    async def test_priority_ordering(self) -> None:
        received_ids = []
        
        def callback(event: Event) -> None:
            received_ids.append(event.payload["id"])

        self.handler.subscribe("task.alert", callback)
        
        self.handler.publish(Event(type="task.alert", payload={"id": "low"}, priority=EventPriority.LOW))
        self.handler.publish(Event(type="task.alert", payload={"id": "critical"}, priority=EventPriority.CRITICAL))
        self.handler.publish(Event(type="task.alert", payload={"id": "normal"}, priority=EventPriority.NORMAL))

        await self.handler.process_pending_events()

        assert received_ids == ["critical", "normal", "low"]

    @pytest.mark.asyncio
    async def test_async_callback_support(self) -> None:
        received = []
        
        async def async_callback(event: Event) -> None:
            await asyncio.sleep(0.01)
            received.append(event.type)

        self.handler.subscribe("async.event", async_callback)
        self.handler.publish(Event(type="async.event"))

        await self.handler.process_pending_events()

        assert len(received) == 1
        assert received[0] == "async.event"

    @pytest.mark.asyncio
    async def test_callback_exception_isolation(self) -> None:
        def failing_callback(event: Event) -> None:
            raise ValueError("Simulated callback failure")

        successful_callback_called = False
        
        def success_callback(event: Event) -> None:
            nonlocal successful_callback_called
            successful_callback_called = True

        self.handler.subscribe("error.event", failing_callback)
        self.handler.subscribe("error.event", success_callback)
        self.handler.publish(Event(type="error.event"))

        await self.handler.process_pending_events()

        assert successful_callback_called is True