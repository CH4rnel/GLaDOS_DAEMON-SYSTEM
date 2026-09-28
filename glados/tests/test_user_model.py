# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS User Modeling subsystem.
Ensures that durable user preferences are extracted, versioned, and stored
locally — fully inspectable, editable, and erasable by the Operator.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from glados.memory.user_model import UserModel, reflect_on_user
from glados.core.context import RuntimeContext


class TestUserModel:
    """Tests for the UserModel Pydantic model."""

    def test_user_model_creation_valid(self):
        """Test creating a valid user model."""
        model = UserModel(
            version=1,
            stable_preferences=["prefers TDD red-green-refactor"],
            working_style=["concise responses", "code-first"],
            last_updated=datetime.now(timezone.utc)
        )
        assert model.version == 1
        assert "TDD" in model.stable_preferences[0]

    def test_user_model_default_empty(self):
        """Test that UserModel can be created with empty defaults."""
        model = UserModel(version=0)
        assert model.stable_preferences == []
        assert model.working_style == []


class TestReflectOnUser:
    """Tests for the reflect_on_user periodic task."""

    @pytest.fixture
    def mock_ctx(self):
        """Simulates RuntimeContext with memory and brain."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.ltm = MagicMock()
        ctx.brain = MagicMock()
        ctx.brain.llm = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.mark.asyncio
    async def test_reflect_extracts_preferences_from_ltm(self, mock_ctx, tmp_path: Path):
        """Test that reflect_on_user extracts stable patterns from recent LTM."""
        # Mock LTM returning recent records
        from glados.memory.models import MemoryRecord
        mock_ctx.memory.ltm.get_recent.return_value = [
            MemoryRecord(content="Operator always asks for TDD tests first", role="system"),
            MemoryRecord(content="Operator prefers concise responses", role="system"),
            MemoryRecord(content="Operator likes code-first explanations", role="assistant"),
        ]
        
        # Mock LLM returning structured preferences
        mock_ctx.brain.llm.complete = AsyncMock(return_value=MagicMock(
            content='{"stable_preferences": ["prefers TDD", "prefers concise"], "working_style": ["code-first"]}'
        ))
        
        model_path = tmp_path / "user_model.json"
        result = await reflect_on_user(mock_ctx, model_path=model_path)
        
        assert result.version == 1
        assert "TDD" in result.stable_preferences[0]
        assert model_path.exists()

    @pytest.mark.asyncio
    async def test_reflect_versions_model_on_update(self, mock_ctx, tmp_path: Path):
        """Test that reflect_on_user increments version on each successful reflection."""
        from glados.memory.models import MemoryRecord
        mock_ctx.memory.ltm.get_recent.return_value = [
            MemoryRecord(content="Test content", role="system"),
        ]
        mock_ctx.brain.llm.complete = AsyncMock(return_value=MagicMock(
            content='{"stable_preferences": ["test"], "working_style": []}'
        ))
        
        model_path = tmp_path / "user_model.json"
        
        # First reflection
        result1 = await reflect_on_user(mock_ctx, model_path=model_path)
        assert result1.version == 1
        
        # Second reflection (should increment version)
        result2 = await reflect_on_user(mock_ctx, model_path=model_path)
        assert result2.version == 2

    @pytest.mark.asyncio
    async def test_reflect_handles_empty_ltm_gracefully(self, mock_ctx, tmp_path: Path):
        """Test that reflect_on_user returns None when LTM is empty."""
        mock_ctx.memory.ltm.get_recent.return_value = []
        
        model_path = tmp_path / "user_model.json"
        result = await reflect_on_user(mock_ctx, model_path=model_path)
        
        assert result is None
        mock_ctx.brain.llm.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_model_persists_and_loads(self, tmp_path: Path):
        """Test that UserModel can be saved to disk and loaded back."""
        from glados.memory.user_model import save_user_model, load_user_model
        
        model = UserModel(
            version=3,
            stable_preferences=["test preference"],
            working_style=["test style"],
            last_updated=datetime.now(timezone.utc)
        )
        
        model_path = tmp_path / "user_model.json"
        save_user_model(model, model_path)
        
        loaded = load_user_model(model_path)
        assert loaded.version == 3
        assert loaded.stable_preferences == ["test preference"]

    @pytest.mark.asyncio
    async def test_user_model_can_be_erased(self, tmp_path: Path):
        """Test that user model can be completely erased (Right to Forget)."""
        from glados.memory.user_model import save_user_model, erase_user_model
        
        model = UserModel(version=1)
        model_path = tmp_path / "user_model.json"
        save_user_model(model, model_path)
        assert model_path.exists()
        
        erase_user_model(model_path)
        assert not model_path.exists()