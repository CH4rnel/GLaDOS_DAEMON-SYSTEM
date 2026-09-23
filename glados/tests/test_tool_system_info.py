# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock

from glados.core.context import RuntimeContext
from glados.security import SecurityPolicy
from glados.tools.builtin.system_info import SystemInfoTool


class TestSystemInfoTool:
    def setup_method(self) -> None:
        self.mock_ctx = MagicMock(spec=RuntimeContext)
        self.mock_ctx.security = MagicMock(spec=SecurityPolicy)
        self.mock_ctx.logger = MagicMock()
        self.tool = SystemInfoTool()

    def test_tool_initialization(self) -> None:
        assert self.tool is not None
        assert self.tool.definition.name == "get_system_info"
        assert "system" in self.tool.definition.description.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_basic_system_info(self) -> None:
        result = await self.tool.execute(self.mock_ctx, {"detail_level": "basic"})
        
        assert isinstance(result, dict)
        assert "os" in result
        assert "python_version" in result
        assert "processor" not in result

    @pytest.mark.asyncio
    async def test_execute_returns_detailed_system_info(self) -> None:
        result = await self.tool.execute(self.mock_ctx, {"detail_level": "detailed"})
        
        assert isinstance(result, dict)
        assert "os" in result
        assert "processor" in result
        assert "platform" in result

    @pytest.mark.asyncio
    async def test_execute_defaults_to_basic(self) -> None:
        result = await self.tool.execute(self.mock_ctx, {})
        
        assert isinstance(result, dict)
        assert "os" in result
        assert "processor" not in result