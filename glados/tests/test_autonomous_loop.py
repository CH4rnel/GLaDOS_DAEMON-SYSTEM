# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Autonomous Loop.
Follows TDD methodology to define the contract for autonomous runtime execution.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from glados.autonomous.loop import AutonomousLoop
from glados.core.context import RuntimeContext
from glados.core.identity import Identity
from glados.memory.manager import MemoryManager
from glados.llm.registry import LLMRegistry
from glados.llm.router import LLMRouter
from glados.autonomous.scheduler import Scheduler
from glados.autonomous.events import EventHandler


class TestAutonomousLoop:
    """Tests for the AutonomousLoop implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.identity = Identity(
            name="GLaDOS",
            codename="Test",
            version="0.1.0",
            owner={"username": "test", "environment": "test"},
            system={"os": "Linux", "arch": "x86_64"},
            purpose="Testing",
            personality={},
            principles=[]
        )
        
        self.memory = MagicMock(spec=MemoryManager)
        self.llm_registry = LLMRegistry()
        self.llm_router = LLMRouter(self.llm_registry)
        self.scheduler = MagicMock(spec=Scheduler)
        self.event_handler = MagicMock(spec=EventHandler)
        
        self.ctx = RuntimeContext(
            identity=self.identity,
            logger=MagicMock(),
            memory=self.memory,
            llm_agents=self.llm_registry,
            llm_router=self.llm_router,
        )

    def test_autonomous_loop_initialization(self):
        """Test that AutonomousLoop can be initialized."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        assert loop is not None
        assert loop.ctx == self.ctx

    def test_autonomous_loop_default_interval(self):
        """Test that AutonomousLoop has default interval."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        assert loop.interval_seconds == 60  # Default 1 minute

    def test_autonomous_loop_custom_interval(self):
        """Test that AutonomousLoop accepts custom interval."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler,
            interval_seconds=30
        )
        assert loop.interval_seconds == 30

    @pytest.mark.asyncio
    async def test_autonomous_loop_run_once(self):
        """Test that run_once executes one iteration."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        
        # Mock the iteration method
        loop._run_iteration = AsyncMock()
        
        await loop.run_once()
        
        loop._run_iteration.assert_called_once()

    @pytest.mark.asyncio
    async def test_autonomous_loop_run_continuous(self):
        """Test that run_continuous executes multiple iterations."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler,
            interval_seconds=0.1  # Fast interval for testing
        )
        
        # Mock the iteration method
        loop._run_iteration = AsyncMock()
        
        # Run for a short time
        task = asyncio.create_task(loop.run_continuous(max_iterations=3))
        await asyncio.sleep(0.5)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Should have called _run_iteration at least once
        assert loop._run_iteration.call_count >= 1

    @pytest.mark.asyncio
    async def test_autonomous_loop_stop(self):
        """Test that stop() gracefully stops the loop."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        
        loop._running = True
        loop.stop()
        
        assert loop._running is False

    @pytest.mark.asyncio
    async def test_autonomous_loop_iteration_calls_scheduler(self):
        """Test that iteration calls scheduler."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        
        self.scheduler.check_and_run_due_tasks = AsyncMock()
        
        await loop._run_iteration()
        
        self.scheduler.check_and_run_due_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_autonomous_loop_iteration_calls_event_handler(self):
        """Test that iteration calls event handler."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        
        self.scheduler.check_and_run_due_tasks = AsyncMock()
        self.event_handler.process_pending_events = AsyncMock()
        
        await loop._run_iteration()
        
        self.event_handler.process_pending_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_autonomous_loop_handles_exceptions_gracefully(self):
        """Test that loop continues even if iteration fails."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        
        loop._running = True
        
        # Make scheduler raise exception
        self.scheduler.check_and_run_due_tasks = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        # Should not raise exception
        await loop._run_iteration()
        
        # Loop should still be running
        assert loop._running is True

    def test_autonomous_loop_status(self):
        """Test that status() returns current state."""
        loop = AutonomousLoop(
            ctx=self.ctx,
            scheduler=self.scheduler,
            event_handler=self.event_handler
        )
        
        status = loop.status()
        
        assert "running" in status
        assert "interval_seconds" in status
        assert "last_iteration" in status
