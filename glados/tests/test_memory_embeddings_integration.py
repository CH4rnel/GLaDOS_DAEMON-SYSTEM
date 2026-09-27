# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for MemoryManager integration with EmbeddingProvider.
Ensures automatic vector generation on persist and semantic search functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from glados.llm.embeddings.base import BaseEmbeddingProvider
from glados.memory.manager import MemoryManager


class TestMemoryEmbeddingsIntegration:
    """Tests for embedding integration in MemoryManager."""

    @pytest.fixture
    def mock_embedding_provider(self):
        """Mock embedding provider that returns predictable vectors."""
        provider = MagicMock(spec=BaseEmbeddingProvider)
        provider.embed = AsyncMock(side_effect=lambda text: [0.1] * 384 if "test" in text else [0.2] * 384)
        return provider

    @pytest.fixture
    def memory_manager(self, tmp_path: Path, mock_embedding_provider):
        """MemoryManager with embedding provider configured."""
        ltm_path = tmp_path / "test_memory.db"
        manager = MemoryManager(
            stm_max_size=10,
            ltm_path=ltm_path,
            embedding_provider=mock_embedding_provider
        )
        return manager

    @pytest.mark.asyncio
    async def test_remember_with_persist_generates_embedding(self, memory_manager, mock_embedding_provider):
        """Test that remember(..., persist=True) automatically generates embedding."""
        await memory_manager.remember("Test memory content", role="user", persist=True)
        
        # Verify embedding was generated
        mock_embedding_provider.embed.assert_called_once_with("Test memory content")
        
        # Verify record in LTM has embedding
        ltm_records = memory_manager.ltm.load_all()
        assert len(ltm_records) == 1
        assert ltm_records[0].embedding is not None
        assert len(ltm_records[0].embedding) == 384

    @pytest.mark.asyncio
    async def test_remember_without_persist_skips_embedding(self, memory_manager, mock_embedding_provider):
        """Test that remember(..., persist=False) does not generate embedding."""
        await memory_manager.remember("Short-term only", role="user", persist=False)
        
        # Embedding should not be called
        mock_embedding_provider.embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_semantic_with_ltm_embeddings(self, memory_manager):
        """Test semantic search across both STM and LTM records."""
        # Add records to LTM with embeddings
        await memory_manager.remember("Python programming", role="user", persist=True)
        await memory_manager.remember("Rust systems programming", role="user", persist=True)
        
        # Query with similar embedding
        query_embedding = [0.1] * 384  # Matches "Python programming"
        results = await memory_manager.search_semantic(query_embedding, top_k=1)
        
        assert len(results) == 1
        assert "Python" in results[0].content

    @pytest.mark.asyncio
    async def test_memory_manager_without_embedding_provider(self, tmp_path: Path):
        """Test graceful degradation when no embedding provider is configured."""
        ltm_path = tmp_path / "test_memory_no_embed.db"
        manager = MemoryManager(stm_max_size=10, ltm_path=ltm_path, embedding_provider=None)
        
        # Should work without embeddings
        await manager.remember("Test without embeddings", role="user", persist=True)
        
        ltm_records = manager.ltm.load_all()
        assert len(ltm_records) == 1
        assert ltm_records[0].embedding is None