# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Short-term memory implementation.
Maintains an in-memory sliding window of recent interactions.
"""

from collections import deque
from loguru import logger

from glados.memory.models import MemoryRecord


class ShortTermMemory:
    """
    In-memory short-term storage.
    Uses a FIFO queue with a maximum capacity to maintain recent context.
    """

    def __init__(self, max_size: int = 50) -> None:
        """
        Initializes the short-term memory buffer.
        
        :param max_size: Maximum number of records to keep in memory.
        """
        self._buffer: deque[MemoryRecord] = deque(maxlen=max_size)
        self.logger = logger.bind(component="ShortTermMemory")
        self.logger.debug(f"ShortTermMemory initialized with max_size={max_size}")

    def add(self, record: MemoryRecord) -> None:
        """Adds a record to the short-term buffer."""
        self._buffer.append(record)
        self.logger.debug(f"Added to STM: {record.role} - {record.content[:30]}...")

    def get_context(self) -> list[MemoryRecord]:
        """Returns the current context as a list of records."""
        return list(self._buffer)

    def clear(self) -> None:
        """Clears the short-term memory buffer."""
        self._buffer.clear()
        self.logger.info("ShortTermMemory cleared.")