# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

"""
Memory Manager.
Acts as a Facade for the memory subsystem, unifying short-term and long-term operations.
"""

import math
from pathlib import Path
from typing import List

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
        self.logger = logger.bind(component="MemoryManager")
        
        self.stm = ShortTermMemory(max_size=stm_max_size)
        
        if ltm_path is None:
            ltm_path = Path("data/long_term_memory.json")
            
        self.ltm = LongTermMemory(storage_path=ltm_path)
        
        self.logger.info("MemoryManager initialized.")

    def remember(self, content: str, role: str = "system", persist: bool = False, metadata: dict | None = None, embedding: list[float] | None = None) -> None:
        record = MemoryRecord(content=content, role=role, metadata=metadata or {}, embedding=embedding)
        self.stm.add(record)
        if persist:
            self.ltm.save(record)
            self.logger.debug(f"Memory persisted to LTM: {content[:30]}...")

    def add_short_term_record(self, role: str, content: str, embedding: list[float] | None = None) -> None:
        """Convenience method to add a record directly to short-term memory."""
        record = MemoryRecord(content=content, role=role, embedding=embedding)
        self.stm.add(record)

    def get_short_term_context(self) -> list[MemoryRecord]:
        return self.stm.get_context()

    def search_long_term(self, query: str) -> list[MemoryRecord]:
        return self.ltm.search(query)

    async def search_semantic(self, query_embedding: list[float], top_k: int = 5, threshold: float = 0.0) -> list[MemoryRecord]:
        """
        Performs semantic search on short-term memory using cosine similarity.
        """
        context = self.stm.get_context()
        scored_records: list[tuple[float, MemoryRecord]] = []
        
        query_norm = math.sqrt(sum(x * x for x in query_embedding))
        if query_norm == 0:
            return []
            
        for record in context:
            if not record.embedding:
                continue
            
            dot_product = sum(q * e for q, e in zip(query_embedding, record.embedding))
            record_norm = math.sqrt(sum(e * e for e in record.embedding))
            
            if record_norm == 0:
                continue
                
            similarity = dot_product / (query_norm * record_norm)
            
            if similarity >= threshold:
                scored_records.append((similarity, record))
                
        scored_records.sort(key=lambda x: x[0], reverse=True)
        
        return [record for _, record in scored_records[:top_k]]