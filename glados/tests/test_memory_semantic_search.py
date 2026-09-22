# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from pathlib import Path

from glados.memory.manager import MemoryManager


class TestMemorySemanticSearch:
    def setup_method(self) -> None:
        self.test_path = Path("data/test_memory.json")
        self.memory = MemoryManager(stm_max_size=10, ltm_path=self.test_path)

    def teardown_method(self) -> None:
        if self.test_path.exists():
            self.test_path.unlink()

    def test_add_record_with_embedding(self) -> None:
        embedding = [0.1, 0.2, 0.3, 0.4]
        
        self.memory.add_short_term_record("user", "Test query about system performance", embedding=embedding)
        
        context = self.memory.get_short_term_context()
        assert len(context) == 1
        assert context[0].embedding == embedding

    @pytest.mark.asyncio
    async def test_semantic_search_returns_similar_records(self) -> None:
        self.memory.add_short_term_record("user", "CPU usage is high", embedding=[1.0, 0.0, 0.0])
        self.memory.add_short_term_record("user", "Memory consumption critical", embedding=[0.0, 1.0, 0.0])
        self.memory.add_short_term_record("user", "Disk space low", embedding=[0.0, 0.0, 1.0])
        
        query_embedding = [0.9, 0.1, 0.0]
        results = await self.memory.search_semantic(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert "CPU" in results[0].content or "Memory" in results[0].content

    @pytest.mark.asyncio
    async def test_semantic_search_returns_empty_for_no_matches(self) -> None:
        self.memory.add_short_term_record("user", "Test record", embedding=[1.0, 0.0, 0.0])
        
        query_embedding = [0.0, 1.0, 0.0]
        results = await self.memory.search_semantic(query_embedding, top_k=1, threshold=0.99)
        
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_semantic_search_handles_empty_memory(self) -> None:
        query_embedding = [0.5, 0.5, 0.5]
        results = await self.memory.search_semantic(query_embedding, top_k=5)
        
        assert len(results) == 0