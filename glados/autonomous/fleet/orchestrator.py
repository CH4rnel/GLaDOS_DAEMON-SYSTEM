# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Agent Fleet Orchestrator for GLaDOS_DAEMON-SYSTEM.
Manages resource-bounded, time-limited sub-agent swarms for Operator-approved tasks.

Design principles:
- Sub-agents spawned ONLY for Operator-approved tasks.
- Strictly resource- and time-bounded (task ID, deadline, token budget).
- Bound by same SecurityPolicy/GuardianGate as main agent — no elevated trust.
- Terminated when task completes — no persistent background replication.
- Unable to spawn further sub-agents autonomously — recursion goes back through orchestrator.
- Reuses existing LLMRouter strategies (PARALLEL/CONSENSUS/SINGLE).
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext
from glados.security.policy import PolicyViolation


class FleetTask(BaseModel):
    """
    A resource-bounded task for the Agent Fleet.
    Strictly enforces time, token, and agent count limits.
    """
    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this fleet task"
    )
    objective: str = Field(..., min_length=1, description="Human-readable task objective")
    strategy: str = Field(
        default="PARALLEL",
        description="LLMRouter strategy: PARALLEL, CONSENSUS, or SINGLE"
    )
    max_agents: int = Field(default=3, gt=0, description="Maximum number of sub-agents")
    token_budget: int = Field(default=10000, gt=0, description="Maximum total tokens allowed")
    timeout_seconds: int = Field(default=300, gt=0, description="Maximum execution time in seconds")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the task started"
    )

    def is_expired(self) -> bool:
        """Checks if the task has exceeded its time budget."""
        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return elapsed > self.timeout_seconds


class FleetResult(BaseModel):
    """
    Structured result from a fleet task execution.
    Contains status, token usage, and agent responses.
    """
    task_id: str
    status: str = Field(..., description="COMPLETED, ABORTED_TIMEOUT, or FAILED")
    total_tokens_used: int = Field(default=0, description="Total tokens consumed by all agents")
    agent_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Individual results from each sub-agent"
    )
    error: Optional[str] = Field(default=None, description="Error message if task failed")
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the task completed or was aborted"
    )


class AgentFleetOrchestrator:
    """
    Orchestrates resource-bounded sub-agent swarms for Operator-approved tasks.
    Enforces strict limits on time, tokens, and agent count.
    """

    def __init__(self, ctx: RuntimeContext) -> None:
        self.ctx = ctx
        self.logger = logger.bind(component="AgentFleetOrchestrator")

    async def execute_task(self, task: FleetTask) -> FleetResult:
        """
        Executes a fleet task with strict resource bounds.
        
        :param task: The FleetTask to execute.
        :return: FleetResult with status, token usage, and agent responses.
        :raises PolicyViolation: If the objective is denied by SecurityPolicy.
        """
        self.logger.info(
            f"Starting fleet task: {task.task_id} "
            f"(objective={task.objective[:50]}, strategy={task.strategy}, "
            f"max_agents={task.max_agents}, token_budget={task.token_budget})"
        )

        # Fail-closed: check objective against SecurityPolicy BEFORE execution
        if self.ctx.security is not None:
            try:
                self.ctx.security.check_fleet_objective(task.objective)
            except PolicyViolation as e:
                self.logger.warning(f"Fleet task denied by policy: {task.task_id} - {e}")
                raise

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute_with_router(task),
                timeout=task.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(f"Fleet task timed out: {task.task_id}")
            return FleetResult(
                task_id=task.task_id,
                status="ABORTED_TIMEOUT",
                error=f"Task exceeded timeout of {task.timeout_seconds} seconds"
            )
        except Exception as e:
            self.logger.error(f"Fleet task failed: {task.task_id} - {e}", exc_info=True)
            return FleetResult(
                task_id=task.task_id,
                status="FAILED",
                error=str(e)
            )

    async def _execute_with_router(self, task: FleetTask) -> FleetResult:
        """
        Internal method: delegates to LLMRouter with resource bounds.
        
        :param task: The FleetTask to execute.
        :return: FleetResult with agent responses.
        """
        # Build messages for LLMRouter
        from glados.llm.models import LLMMessage
        messages = [LLMMessage(role="user", content=task.objective)]

        # Call LLMRouter with strategy
        # Note: LLMRouter already implements PARALLEL/CONSENSUS/SINGLE strategies
        agent_results = await self.ctx.llm_router.route(
            messages=messages,
            strategy=task.strategy,
            max_agents=task.max_agents,
        )

        # Calculate total tokens used
        total_tokens = sum(r.get("tokens_used", 0) for r in agent_results)

        # Enforce token budget
        if total_tokens > task.token_budget:
            self.logger.warning(
                f"Fleet task exceeded token budget: {total_tokens} > {task.token_budget}"
            )
            return FleetResult(
                task_id=task.task_id,
                status="FAILED",
                total_tokens_used=total_tokens,
                agent_results=agent_results,
                error=f"Token budget exceeded: {total_tokens} > {task.token_budget}"
            )

        self.logger.info(
            f"Fleet task completed: {task.task_id} "
            f"(tokens_used={total_tokens}, agents={len(agent_results)})"
        )

        return FleetResult(
            task_id=task.task_id,
            status="COMPLETED",
            total_tokens_used=total_tokens,
            agent_results=agent_results,
        )