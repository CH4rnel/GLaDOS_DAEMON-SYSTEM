# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

from glados.core.event import Event


@dataclass
class EventHandler:
    """Manages event subscriptions and processes events based on priority."""
    
    _subscribers: Dict[str, List[Callable[[Event], None]]] = field(default_factory=lambda: defaultdict(list))
    _queue: List[Tuple[int, int, Event]] = field(default_factory=list)
    _counter: int = 0

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Registers a callback for a specific event type."""
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        """Adds an event to the priority queue."""
        heapq.heappush(self._queue, (event.priority.value, self._counter, event))
        self._counter += 1

    def has_pending_events(self) -> bool:
        """Checks if there are any unprocessed events in the queue."""
        return len(self._queue) > 0

    def process_next(self) -> None:
        """Processes the highest priority event from the queue."""
        if not self._queue:
            return

        _, _, event = heapq.heappop(self._queue)
        
        for callback in self._subscribers.get(event.type, []):
            callback(event)