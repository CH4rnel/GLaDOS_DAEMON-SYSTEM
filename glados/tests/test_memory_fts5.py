# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the FTS5 (Full-Text Search) implementation in LongTermMemory.
Ensures that SQLite virtual tables correctly index and retrieve memory records.
"""

import pytest
from pathlib import Path

from glados.memory.models import MemoryRecord
from glados.memory.long_term import LongTermMemory


class TestLongTermMemoryFTS5:
    """Tests for SQLite FTS5 integration in LongTermMemory."""

    @pytest.fixture
    def db_path(self, tmp_path: Path) -> Path:
        return tmp_path / "test_fts5_memory.db"

    def test_initialization_creates_tables(self, db_path: Path):
        """Test that initializing LTM creates the necessary SQLite tables."""
        ltm = LongTermMemory(storage_path=db_path)
        
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert "memory_records" in tables
            assert "memory_fts" in tables

    def test_save_and_search_basic(self, db_path: Path):
        """Test that saved records are found via FTS5 MATCH."""
        ltm = LongTermMemory(storage_path=db_path)
        
        ltm.save(MemoryRecord(content="Arch Linux is a highly customizable distribution", role="system"))
        ltm.save(MemoryRecord(content="Python is a versatile programming language", role="system"))
        
        results = ltm.search("Arch Linux")
        
        assert len(results) == 1
        assert "Arch Linux" in results[0].content

    def test_search_handles_special_characters(self, db_path: Path):
        """Test that FTS5 search gracefully handles quotes and special chars."""
        ltm = LongTermMemory(storage_path=db_path)
        
        ltm.save(MemoryRecord(content="Error: 'Connection refused' on port 8080", role="system"))
        
        # FTS5 can be sensitive to quotes; the implementation should sanitize or handle this
        results = ltm.search("Connection refused")
        
        assert len(results) == 1
        assert "port 8080" in results[0].content

    def test_search_returns_empty_for_no_matches(self, db_path: Path):
        """Test that search returns an empty list when no records match."""
        ltm = LongTermMemory(storage_path=db_path)
        
        ltm.save(MemoryRecord(content="System initialized successfully", role="system"))
        
        results = ltm.search("nonexistent keyword xyz123")
        
        assert len(results) == 0

    def test_load_all_preserves_metadata_and_embeddings(self, db_path: Path):
        """Test that load_all correctly deserializes complex fields."""
        ltm = LongTermMemory(storage_path=db_path)
        
        record = MemoryRecord(
            content="Complex record",
            role="user",
            metadata={"source": "test", "priority": 1},
            embedding=[0.1, 0.2, 0.3]
        )
        ltm.save(record)
        
        loaded_records = ltm.load_all()
        
        assert len(loaded_records) == 1
        assert loaded_records[0].metadata == {"source": "test", "priority": 1}
        assert loaded_records[0].embedding == [0.1, 0.2, 0.3]