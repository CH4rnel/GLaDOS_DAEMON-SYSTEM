# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from unittest.mock import MagicMock, AsyncMock

from glados.core.context import RuntimeContext
from glados.core.event import Event
from glados.autonomous.events import EventHandler
from glados.autonomous.tasks.diagnostics_tasks import run_system_diagnostics


class TestDiagnosticsTasks:
    @pytest.mark.asyncio
    async def test_diagnostics_passes_when_all_subsystems_available(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = MagicMock()
        ctx.memory.add_short_term_record = MagicMock()
        ctx.llm_registry = MagicMock()
        ctx.tools = MagicMock()
        
        event_handler = MagicMock(spec=EventHandler)
        
        await run_system_diagnostics(ctx, event_handler)
        
        ctx.memory.add_short_term_record.assert_called_once()
        event_handler.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_diagnostics_publishes_event_when_memory_missing(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = None
        ctx.llm_registry = MagicMock()
        ctx.tools = MagicMock()
        
        event_handler = MagicMock(spec=EventHandler)
        
        await run_system_diagnostics(ctx, event_handler)
        
        event_handler.publish.assert_called_once()
        published_event = event_handler.publish.call_args[0][0]
        assert published_event.type == "system.health_check.failed"
        assert "Memory" in published_event.payload["failed_components"]

    @pytest.mark.asyncio
    async def test_diagnostics_handles_multiple_failures(self) -> None:
        ctx = MagicMock(spec=RuntimeContext)
        ctx.memory = None
        ctx.llm_registry = None
        ctx.tools = MagicMock()
        
        event_handler = MagicMock(spec=EventHandler)
        
        await run_system_diagnostics(ctx, event_handler)
        
        event_handler.publish.assert_called_once()
        published_event = event_handler.publish.call_args[0][0]
        assert "Memory" in published_event.payload["failed_components"]
        assert "LLM Registry" in published_event.payload["failed_components"]