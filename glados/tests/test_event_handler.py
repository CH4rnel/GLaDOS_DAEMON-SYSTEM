# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from glados.core.event import Event, EventPriority
from glados.core.event_handler import EventHandler


class TestEventHandler:
    def test_subscribe_and_publish(self) -> None:
        handler = EventHandler()
        received_events = []

        def callback(event: Event) -> None:
            received_events.append(event)

        handler.subscribe("system.boot", callback)
        event = Event(type="system.boot", payload={"status": "ok"})
        handler.publish(event)

        handler.process_next()

        assert len(received_events) == 1
        assert received_events[0].type == "system.boot"

    def test_priority_ordering(self) -> None:
        handler = EventHandler()
        processed_ids = []

        def callback(event: Event) -> None:
            processed_ids.append(event.payload["id"])

        handler.subscribe("task.run", callback)
        
        handler.publish(Event(type="task.run", payload={"id": "low"}, priority=EventPriority.LOW))
        handler.publish(Event(type="task.run", payload={"id": "critical"}, priority=EventPriority.CRITICAL))
        handler.publish(Event(type="task.run", payload={"id": "normal"}, priority=EventPriority.NORMAL))

        while handler.has_pending_events():
            handler.process_next()

        assert processed_ids == ["critical", "normal", "low"]

    def test_no_subscribers_for_event_type(self) -> None:
        handler = EventHandler()
        handler.publish(Event(type="unknown.event"))
        
        handler.process_next()
        assert not handler.has_pending_events()