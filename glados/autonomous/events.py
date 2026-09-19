# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import asyncio
import heapq
import inspect
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple

from loguru import logger

from glados.core.event import Event

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


class EventHandler:
    """
    Asynchronous event handler for processing system events.
    Utilizes a priority queue to ensure critical events are processed first.
    """

    def __init__(self, ctx: "RuntimeContext") -> None:
        self.ctx = ctx
        self.logger = logger.bind(component="EventHandler")
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = defaultdict(list)
        self._queue: List[Tuple[int, int, Event]] = []
        self._counter: int = 0
        self.logger.debug("Async EventHandler initialized")

    def subscribe(self, event_type: str, callback: Callable[[Event], Any]) -> None:
        """Registers a callback for a specific event type."""
        self._subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to event type: {event_type}")

    def publish(self, event: Event) -> None:
        """Adds an event to the priority queue."""
        heapq.heappush(self._queue, (event.priority.value, self._counter, event))
        self._counter += 1
        self.logger.debug(f"Published event: {event.type} (Priority: {event.priority.name})")

    async def process_pending_events(self) -> None:
        """Processes all pending events in priority order."""
        while self._queue:
            _, _, event = heapq.heappop(self._queue)
            self.logger.debug(f"Processing event: {event.type} (ID: {event.id})")
            
            callbacks = self._subscribers.get(event.type, [])
            for callback in callbacks:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event.type}: {e}", exc_info=True)