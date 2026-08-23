# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS Memory subsystem.
Follows TDD methodology to define the contract for Short-term and Persistent memory.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

# These imports will fail initially (Red Phase) until we implement the modules
from glados.memory.models import MemoryRecord
from glados.memory.short_term import ShortTermMemory
from glados.memory.long_term import LongTermMemory
from glados.memory.manager import MemoryManager


class TestMemoryRecord:
    """Tests for the MemoryRecord Pydantic model."""

    def test_memory_record_creation_valid(self):
        """Test creating a valid memory record."""
        record = MemoryRecord(content="System initialized", role="system")
        assert record.content == "System initialized"
        assert record.role == "system"
        assert isinstance(record.timestamp, datetime)
        assert record.id is not None

    def test_memory_record_invalid_role(self):
        """Test that an invalid role raises ValidationError."""
        with pytest.raises(ValidationError):
            MemoryRecord(content="Test", role="invalid_role")


class TestShortTermMemory:
    """Tests for the ShortTermMemory (in-memory context)."""

    def test_short_term_memory_add_and_get(self):
        """Test adding records and retrieving context."""
        stm = ShortTermMemory(max_size=3)
        stm.add(MemoryRecord(content="Msg 1", role="user"))
        stm.add(MemoryRecord(content="Msg 2", role="assistant"))
        
        context = stm.get_context()
        assert len(context) == 2
        assert context[0].content == "Msg 1"

    def test_short_term_memory_max_size_limit(self):
        """Test that STM respects the maximum size limit (FIFO)."""
        stm = ShortTermMemory(max_size=2)
        stm.add(MemoryRecord(content="Msg 1", role="user"))
        stm.add(MemoryRecord(content="Msg 2", role="user"))
        stm.add(MemoryRecord(content="Msg 3", role="user")) # Should evict Msg 1
        
        context = stm.get_context()
        assert len(context) == 2
        assert context[0].content == "Msg 2"
        assert context[1].content == "Msg 3"


class TestLongTermMemory:
    """Tests for the LongTermMemory (persistent JSON storage)."""

    def test_long_term_memory_save_and_load(self, tmp_path: Path):
        """Test saving records to disk and loading them back."""
        db_path = tmp_path / "test_memory.json"
        ltm = LongTermMemory(storage_path=db_path)
        
        record = MemoryRecord(content="Persistent fact", role="system")
        ltm.save(record)
        
        # Create a new instance to simulate restart
        ltm_reloaded = LongTermMemory(storage_path=db_path)
        records = ltm_reloaded.load_all()
        
        assert len(records) == 1
        assert records[0].content == "Persistent fact"

    def test_long_term_memory_search(self, tmp_path: Path):
        """Test basic keyword search in persistent memory."""
        db_path = tmp_path / "test_memory.json"
        ltm = LongTermMemory(storage_path=db_path)
        
        ltm.save(MemoryRecord(content="Arch Linux is great", role="system"))
        ltm.save(MemoryRecord(content="Python is awesome", role="system"))
        ltm.save(MemoryRecord(content="GLaDOS is watching", role="system"))
        
        results = ltm.search("Linux")
        assert len(results) == 1
        assert "Arch Linux" in results[0].content


class TestMemoryManager:
    """Tests for the unified MemoryManager."""

    def test_memory_manager_integration(self, tmp_path: Path):
        """Test that Manager correctly delegates to STM and LTM."""
        db_path = tmp_path / "manager_memory.json"
        manager = MemoryManager(stm_max_size=10, ltm_path=db_path)
        
        manager.remember("User prefers dark mode", role="user", persist=True)
        
        # Should be in STM
        stm_context = manager.get_short_term_context()
        assert len(stm_context) == 1
        
        # Should be in LTM
        ltm_results = manager.search_long_term("dark mode")
        assert len(ltm_results) == 1