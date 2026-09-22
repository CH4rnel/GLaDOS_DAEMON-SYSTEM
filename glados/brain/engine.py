# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from loguru import logger

from glados.brain.models import TaskInput, ExecutionResult
from glados.brain.planner import Planner

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


class BrainEngine:
    """
    Central orchestration component for task processing and decision making.
    Coordinates memory retrieval, planning, LLM analysis, and tool execution.
    """

    def __init__(self, ctx: "RuntimeContext") -> None:
        self.ctx = ctx
        self.planner = Planner(ctx)
        self.logger = logger.bind(component="BrainEngine")
        self.logger.info("BrainEngine initialized")

    async def process_task(self, task_input: TaskInput) -> ExecutionResult:
        """
        Processes a task through the cognitive pipeline.
        
        :param task_input: Task description and metadata
        :return: Execution result with success status and data
        """
        self.logger.info(f"Processing task: {task_input.description}")
        
        if not task_input.description or not task_input.description.strip():
            self.logger.warning("Task description is empty")
            return ExecutionResult(
                success=False,
                message="Task description cannot be empty",
                data={}
            )
        
        try:
            # 1. Retrieve context from memory
            context: List[Dict[str, Any]] = []
            if self.ctx.memory:
                context = self.ctx.memory.get_short_term_context()
                self.logger.debug(f"Retrieved {len(context)} context records from memory")
            
            # 2. Create execution plan
            plan = await self.planner.create_plan(task_input)
            self.logger.debug(f"Generated plan with {len(plan.steps)} step(s)")
            
            # TODO: 
            # 3. Analyze task with LLM using retrieved context
            # 4. Execute plan steps via GuardianGate
            # 5. Store results in memory
            
            return ExecutionResult(
                success=True,
                message=f"Task acknowledged: {task_input.description}",
                data={
                    "priority": task_input.priority,
                    "context": context,
                    "plan_steps_count": len(plan.steps)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Task processing failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Task processing error: {str(e)}",
                data={}
            )