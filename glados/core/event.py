# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict


class EventPriority(IntEnum):
    """Priority levels for events. Lower value means higher priority."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Event:
    """Represents a system or internal event."""
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)