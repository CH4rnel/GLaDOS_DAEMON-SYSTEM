# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Agent Fleet Orchestrator.
Ensures that sub-agents are strictly bounded by time, tokens, and security policies,
and are terminated upon task completion without autonomous replication.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from glados.autonomous.fleet.orchestrator import AgentFleetOrchestrator, FleetTask
from glados.core.context import RuntimeContext
from glados.llm.router import LLMRouter
from glados.security.policy import PolicyViolation


class TestFleetTask:
    """Tests for the FleetTask data model."""

    def test_task_creation_with_bounds(self):
        """Test creating a task with strict resource bounds."""
        task = FleetTask(
            task_id="task-001",
            objective="Analyze security logs for anomalies",
            strategy="PARALLEL",
            max_agents=3,
            token_budget=5000,
            timeout_seconds=120,
        )
        assert task.task_id == "task-001"
        assert task.strategy == "PARALLEL"
        assert task.max_agents == 3

    def test_task_expiration_check(self):
        """Test that task correctly identifies when it has expired."""
        task = FleetTask(
            task_id="task-002",
            objective="Quick check",
            strategy="SINGLE",
            max_agents=1,
            token_budget=1000,
            timeout_seconds=60,
        )
        # Simulate time passing
        task.started_at = datetime.now(timezone.utc) - timedelta(seconds=120)
        assert task.is_expired() is True


class TestAgentFleetOrchestrator:
    """Tests for the AgentFleetOrchestrator workflow."""

    @pytest.fixture
    def mock_ctx(self):
        """Simulates RuntimeContext with LLMRouter and GuardianGate."""
        ctx = MagicMock(spec=RuntimeContext)
        # Use spec=LLMRouter to prevent automatic attribute creation
        ctx.llm_router = MagicMock(spec=LLMRouter)
        ctx.security = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.fixture
    def orchestrator(self, mock_ctx):
        return AgentFleetOrchestrator(ctx=mock_ctx)

    @pytest.mark.asyncio
    async def test_execute_parallel_task_within_bounds(self, orchestrator, mock_ctx):
        """Test that a parallel task executes and respects token bounds."""
        task = FleetTask(
            task_id="task-003",
            objective="Parallel analysis",
            strategy="PARALLEL",
            max_agents=2,
            token_budget=10000,
            timeout_seconds=300,
        )
        
        # Mock LLMRouter returning bounded results
        mock_ctx.llm_router.route = AsyncMock(return_value=[
            {"agent_id": "agent-1", "content": "Result 1", "tokens_used": 500},
            {"agent_id": "agent-2", "content": "Result 2", "tokens_used": 600},
        ])
        
        result = await orchestrator.execute_task(task)
        
        assert result.task_id == "task-003"
        assert result.status == "COMPLETED"
        assert result.total_tokens_used == 1100
        assert result.total_tokens_used <= task.token_budget

    @pytest.mark.asyncio
    async def test_execute_task_rejected_by_security_policy(self, orchestrator, mock_ctx):
        """Test that fleet execution is blocked if GuardianGate denies the objective."""
        task = FleetTask(
            task_id="task-004",
            objective="Execute unauthorized shell script",
            strategy="SINGLE",
            max_agents=1,
            token_budget=1000,
            timeout_seconds=60,
        )
        
        mock_ctx.security.check_fleet_objective.side_effect = PolicyViolation(
            "Objective contains disallowed shell execution patterns"
        )
        
        with pytest.raises(PolicyViolation):
            await orchestrator.execute_task(task)
        
        mock_ctx.llm_router.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_task_aborts_on_timeout(self, orchestrator, mock_ctx):
        """Test that a task is aborted if it exceeds its time budget."""
        task = FleetTask(
            task_id="task-005",
            objective="Long running task",
            strategy="PARALLEL",
            max_agents=2,
            token_budget=5000,
            timeout_seconds=1,  # Very short timeout for testing
        )
        
        async def slow_route(*args, **kwargs):
            import asyncio
            await asyncio.sleep(5)
            return [{"agent_id": "agent-1", "content": "Result", "tokens_used": 100}]
            
        mock_ctx.llm_router.route.side_effect = slow_route
        
        result = await orchestrator.execute_task(task)
        
        # Contract: result status must be ABORTED_TIMEOUT
        assert result.status == "ABORTED_TIMEOUT"
        assert result.task_id == "task-005"
        assert "timeout" in result.error.lower()
        
        # LLMRouter should NOT have been awaited to completion
        # (the timeout cancels the coroutine)

    @pytest.mark.asyncio
    async def test_no_autonomous_replication(self, orchestrator, mock_ctx):
        """Test that a sub-agent cannot spawn further sub-agents autonomously."""
        # The orchestrator is the ONLY entry point for task creation.
        # Sub-agents (handled by LLMRouter) do not have access to AgentFleetOrchestrator.
        # This test verifies the architectural boundary by checking LLMRouter spec.
        
        # LLMRouter should only have 'route' method, not 'spawn_fleet'
        assert hasattr(orchestrator.ctx.llm_router, "route")
        
        # Verify that LLMRouter class does not define spawn_fleet
        from glados.llm.router import LLMRouter
        assert not hasattr(LLMRouter, "spawn_fleet")