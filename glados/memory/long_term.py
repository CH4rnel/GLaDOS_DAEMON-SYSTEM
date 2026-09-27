# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Long-term memory implementation.
Provides persistent storage using SQLite with FTS5 (Full-Text Search) 
for efficient and scalable keyword retrieval.
"""

import json
import sqlite3
from pathlib import Path
from typing import List

from loguru import logger

from glados.memory.models import MemoryRecord


class LongTermMemory:
    """
    Persistent long-term storage using SQLite.
    Utilizes a standard table for structured data and an FTS5 virtual table 
    for high-performance full-text search on memory content.
    """

    def __init__(self, storage_path: Path) -> None:
        """
        Initializes the long-term storage and sets up the database schema.
        
        :param storage_path: Path to the SQLite database file.
        """
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="LongTermMemory")
        
        self._init_db()
        self.logger.debug(f"LongTermMemory (SQLite/FTS5) initialized at {self._path}")

    def _init_db(self) -> None:
        """Creates the necessary tables and FTS5 virtual table if they do not exist."""
        with sqlite3.connect(self._path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            
            # Source of truth: structured data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_records (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    role TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    embedding TEXT
                )
            """)
            
            # FTS5 virtual table: search index only
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    id UNINDEXED,
                    content
                )
            """)
            conn.commit()

    def save(self, record: MemoryRecord) -> None:
        """
        Appends or updates a record in persistent storage and updates the FTS5 index.
        """
        with sqlite3.connect(self._path) as conn:
            cursor = conn.cursor()
            
            metadata_json = json.dumps(record.metadata) if record.metadata else "{}"
            embedding_json = json.dumps(record.embedding) if record.embedding else None
            timestamp_str = record.timestamp.isoformat()
            
            # Insert into structured table
            cursor.execute("""
                INSERT OR REPLACE INTO memory_records 
                (id, content, role, timestamp, metadata, embedding)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (record.id, record.content, record.role, timestamp_str, metadata_json, embedding_json))
            
            # Synchronize FTS5 index
            cursor.execute("DELETE FROM memory_fts WHERE id = ?", (record.id,))
            cursor.execute("""
                INSERT INTO memory_fts (id, content)
                VALUES (?, ?)
            """, (record.id, record.content))
            
            conn.commit()
            
        self.logger.debug(f"Saved to LTM (FTS5): {record.content[:30]}...")

    def load_all(self) -> List[MemoryRecord]:
        """Loads all records from persistent storage."""
        with sqlite3.connect(self._path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, role, timestamp, metadata, embedding FROM memory_records")
            rows = cursor.fetchall()
            
        return [self._row_to_record(row) for row in rows]

    def search(self, query: str) -> List[MemoryRecord]:
        """
        Performs a full-text search using SQLite FTS5 MATCH.
        Sanitizes the query to prevent FTS5 syntax errors from user input.
        """
        if not query.strip():
            return []
            
        # Sanitize query: escape double quotes to prevent FTS5 phrase parsing errors
        sanitized_query = query.replace('"', '""')
        fts_query = f'"{sanitized_query}"'
        
        with sqlite3.connect(self._path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Join FTS5 index with structured data to retrieve full records
            cursor.execute("""
                SELECT m.id, m.content, m.role, m.timestamp, m.metadata, m.embedding
                FROM memory_fts f
                JOIN memory_records m ON f.id = m.id
                WHERE memory_fts MATCH ?
                ORDER BY rank
            """, (fts_query,))
            
            rows = cursor.fetchall()
            
        return [self._row_to_record(row) for row in rows]

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        """Deserializes a database row into a MemoryRecord object."""
        return MemoryRecord(
            id=row["id"],
            content=row["content"],
            role=row["role"],
            timestamp=row["timestamp"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            embedding=json.loads(row["embedding"]) if row["embedding"] else None
        )