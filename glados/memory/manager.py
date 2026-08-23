# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Memory Manager.
Acts as a Facade for the memory subsystem, unifying short-term and long-term operations.
"""

from pathlib import Path
from loguru import logger

from glados.memory.models import MemoryRecord
from glados.memory.short_term import ShortTermMemory
from glados.memory.long_term import LongTermMemory


class MemoryManager:
    """
    Central interface for the memory subsystem.
    Coordinates interactions between STM and LTM.
    """

    def __init__(self, stm_max_size: int = 50, ltm_path: Path | None = None) -> None:
        """
        Initializes the Memory Manager and its underlying storages.
        
        :param stm_max_size: Capacity for short-term memory.
        :param ltm_path: File path for long-term persistent storage.
        """
        self.logger = logger.bind(component="MemoryManager")
        
        self.stm = ShortTermMemory(max_size=stm_max_size)
        
        # Default LTM path if not provided
        if ltm_path is None:
            ltm_path = Path("data/long_term_memory.json")
            
        self.ltm = LongTermMemory(storage_path=ltm_path)
        
        self.logger.info("MemoryManager initialized.")

    def remember(self, content: str, role: str = "system", persist: bool = False, metadata: dict | None = None) -> None:
        """
        Stores a new memory.
        
        :param content: The content to remember.
        :param role: The role (user, assistant, system).
        :param persist: Whether to also save to long-term storage.
        :param metadata: Optional metadata.
        """
        record = MemoryRecord(content=content, role=role, metadata=metadata or {})
        
        # Always add to short-term context
        self.stm.add(record)
        
        # Conditionally persist to long-term
        if persist:
            self.ltm.save(record)
            self.logger.debug(f"Memory persisted to LTM: {content[:30]}...")

    def get_short_term_context(self) -> list[MemoryRecord]:
        """Retrieves the current short-term context."""
        return self.stm.get_context()

    def search_long_term(self, query: str) -> list[MemoryRecord]:
        """Searches the long-term memory for relevant records."""
        return self.ltm.search(query)