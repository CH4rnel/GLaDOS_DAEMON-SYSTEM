# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Brain Engine module for GLaDOS_DAEMON-SYSTEM.
Responsible for orchestrating task processing, planning, and execution.
"""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext
from glados.brain.planner import Planner, Plan


class TaskInput(BaseModel):
    """Input task model for validation and structuring."""
    description: str = Field(..., min_length=1, description="Task description from user or system")
    priority: int = Field(default=1, ge=1, le=5, description="Task priority (1-5)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExecutionResult(BaseModel):
    """Task execution result model."""
    success: bool = Field(..., description="Success flag")
    message: str = Field(..., description="Human-readable result message")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured result data")


class BrainEngine:
    """
    Central orchestrator of the GLaDOS system.
    Manages the task processing lifecycle: from receiving to planning and execution.
    """

    def __init__(self, ctx: RuntimeContext) -> None:
        """
        Initializes the BrainEngine using dependency injection.
        
        :param ctx: Global execution context containing Identity, Logger, and Memory.
        """
        self._ctx = ctx
        self.logger = ctx.logger.bind(component="BrainEngine")
        
        # Initialize Phase 2 subsystems
        self.planner = Planner()
        
        self.logger.debug("BrainEngine initialized successfully with Planner and Memory access.")

    async def process_task(self, task: TaskInput) -> ExecutionResult:
        """
        Processes an incoming task. Orchestrates memory, planning, and execution.
        
        :param task: Validated input task model.
        :return: Structured execution result.
        """
        self.logger.info(
            "Processing task", 
            task_description=task.description, 
            priority=task.priority
        )

        try:
            # ---------------------------------------------------------
            # Phase 3: Memory Integration
            # ---------------------------------------------------------
            # 1. Remember the incoming task in short-term and long-term memory
            self._ctx.memory.remember(
                content=f"Task received: {task.description}", 
                role="user", 
                persist=True,
                metadata={"priority": task.priority, **task.metadata}
            )
            
            # 2. Retrieve relevant past context from long-term memory
            past_context = self._ctx.memory.search_long_term(task.description)
            if past_context:
                self.logger.info(f"Enriched context: found {len(past_context)} relevant past memories.")
            
            # ---------------------------------------------------------
            # Phase 2: Planning Subsystem
            # ---------------------------------------------------------
            # 3. Generate an execution plan based on the task
            plan: Plan = self.planner.create_plan(task)
            self.logger.info(f"Plan generated with {len(plan.steps)} steps.")
            
            # 4. Remember the generated plan in short-term memory (transient state)
            self._ctx.memory.remember(
                content=f"Plan generated: {len(plan.steps)} steps for '{task.description}'", 
                role="assistant", 
                persist=False
            )
            
            # ---------------------------------------------------------
            # TODO (Phase 4-5): Execute skills and tools based on the plan
            # ---------------------------------------------------------
            
            result_message = (
                f"Task '{task.description}' planned successfully. "
                f"Context enriched with {len(past_context)} memories. Awaiting execution phase."
            )
            
            return ExecutionResult(
                success=True,
                message=result_message,
                data={
                    "status": "planned",
                    "plan_steps_count": len(plan.steps),
                    "memories_found": len(past_context)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process task: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Internal BrainEngine error: {str(e)}",
                data={"error_type": type(e).__name__}
            )