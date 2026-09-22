# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from glados.core.context import RuntimeContext
from glados.skills.registry import SkillRegistry
from glados.skills.loader import SkillLoader


class TestBuiltinSkills:
    def setup_method(self) -> None:
        self.registry = SkillRegistry()
        builtin_dir = Path("glados/skills/builtin")
        self.loader = SkillLoader(skills_dir=builtin_dir)
        self.loader.load_all(self.registry)
        
        self.mock_ctx = MagicMock(spec=RuntimeContext)
        self.mock_ctx.logger = MagicMock()

    def test_echo_skill_is_loaded(self) -> None:
        skill = self.registry.get("echo")
        assert skill is not None
        assert skill.definition.name == "echo"
        assert "echo" in skill.definition.description.lower()

    @pytest.mark.asyncio
    async def test_echo_skill_execution(self) -> None:
        skill = self.registry.get("echo")
        result = await skill.execute(self.mock_ctx, {"input_text": "test message"})
        assert result == "Echo: test message"

    def test_get_timestamp_skill_is_loaded(self) -> None:
        skill = self.registry.get("get_timestamp")
        assert skill is not None
        assert skill.definition.name == "get_timestamp"
        assert "timestamp" in skill.definition.description.lower()

    @pytest.mark.asyncio
    async def test_get_timestamp_skill_execution(self) -> None:
        skill = self.registry.get("get_timestamp")
        result = await skill.execute(self.mock_ctx, {})
        assert isinstance(result, str)
        parsed = datetime.fromisoformat(result)
        assert isinstance(parsed, datetime)

    def test_word_count_skill_is_loaded(self) -> None:
        skill = self.registry.get("word_count")
        assert skill is not None
        assert skill.definition.name == "word_count"
        assert "word" in skill.definition.description.lower()

    @pytest.mark.asyncio
    async def test_word_count_skill_execution(self) -> None:
        skill = self.registry.get("word_count")
        result = await skill.execute(self.mock_ctx, {"text": "this is a test message with seven words"})
        assert result == 8

    @pytest.mark.asyncio
    async def test_word_count_handles_empty_string(self) -> None:
        skill = self.registry.get("word_count")
        result = await skill.execute(self.mock_ctx, {"text": ""})
        assert result == 0

    @pytest.mark.asyncio
    async def test_word_count_handles_whitespace(self) -> None:
        skill = self.registry.get("word_count")
        result = await skill.execute(self.mock_ctx, {"text": "   "})
        assert result == 0