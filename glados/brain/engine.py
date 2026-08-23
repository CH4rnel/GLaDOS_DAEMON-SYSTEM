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
        
        :param ctx: Global execution context containing Identity and Logger.
        """
        self._ctx = ctx
        self.logger = ctx.logger.bind(component="BrainEngine")
        
        # Initialize subsystems
        self.planner = Planner()
        
        self.logger.debug("BrainEngine initialized successfully with Planner.")

    async def process_task(self, task: TaskInput) -> ExecutionResult:
        """
        Processes an incoming task. Orchestrates planning, memory, and execution.
        
        :param task: Validated input task model.
        :return: Structured execution result.
        """
        self.logger.info(
            "Processing task", 
            task_description=task.description, 
            priority=task.priority
        )

        try:
            # Phase 2: Planning
            plan: Plan = self.planner.create_plan(task)
            self.logger.info(f"Plan generated with {len(plan.steps)} steps.")
            
            # TODO (Phase 3): Query memory subsystem (Memory) here
            # TODO (Phase 4-5): Execute skills and tools (Skills/Tools) here based on the plan
            
            result_message = f"Task '{task.description}' planned successfully. Awaiting execution phase."
            
            return ExecutionResult(
                success=True,
                message=result_message,
                data={
                    "status": "planned",
                    "plan_steps_count": len(plan.steps)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process task: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Internal BrainEngine error: {str(e)}",
                data={"error_type": type(e).__name__}
            )