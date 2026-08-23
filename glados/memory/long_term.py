# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀 𓂀  ☿ ♃

"""
Long-term memory implementation.
Provides persistent storage using local JSON files.
"""

import json
from pathlib import Path
from loguru import logger

from glados.memory.models import MemoryRecord


class LongTermMemory:
    """
    Persistent long-term storage.
    Currently uses a local JSON file. Designed to be extended with 
    vector databases or SQLite for semantic search in the future.
    """

    def __init__(self, storage_path: Path) -> None:
        """
        Initializes the long-term storage.
        
        :param storage_path: Path to the JSON file for persistence.
        """
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="LongTermMemory")
        
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")
            
        self.logger.debug(f"LongTermMemory initialized at {self._path}")

    def save(self, record: MemoryRecord) -> None:
        """Appends a record to the persistent storage."""
        records = self._load_raw()
        records.append(record.model_dump(mode="json"))
        self._save_raw(records)
        self.logger.debug(f"Saved to LTM: {record.content[:30]}...")

    def load_all(self) -> list[MemoryRecord]:
        """Loads all records from persistent storage."""
        raw_data = self._load_raw()
        return [MemoryRecord.model_validate(item) for item in raw_data]

    def search(self, query: str) -> list[MemoryRecord]:
        """
        Performs a basic keyword search.
        TODO (Phase 3+): Replace with semantic/vector search.
        """
        results = []
        query_lower = query.lower()
        for record in self.load_all():
            if query_lower in record.content.lower():
                results.append(record)
        return results

    def _load_raw(self) -> list[dict]:
        """Internal method to read raw JSON data."""
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            self.logger.warning("Corrupted memory file. Resetting.")
            return []

    def _save_raw(self, data: list[dict]) -> None:
        """Internal method to write raw JSON data."""
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")