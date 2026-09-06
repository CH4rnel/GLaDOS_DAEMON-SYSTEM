# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Brain Engine module for GLaDOS_DAEMON-SYSTEM.
Responsible for orchestrating task processing, planning, and execution.
"""

from glados.core.context import RuntimeContext
from glados.brain.models import TaskInput, ExecutionResult
from glados.brain.planner import Planner, Plan


class BrainEngine:
    """
    Central orchestrator of the GLaDOS system.
    Manages the task processing lifecycle: from receiving to planning and execution.
    """

    def __init__(self, ctx: RuntimeContext) -> None:
        self._ctx = ctx
        self.logger = ctx.logger.bind(component="BrainEngine")
        self.planner = Planner()
        self.logger.debug("BrainEngine initialized successfully with Planner and Memory access.")

    async def process_task(self, task: TaskInput) -> ExecutionResult:
        """Processes an incoming task. Orchestrates memory, planning, and execution."""
        self.logger.info("Processing task", task_description=task.description, priority=task.priority)

        try:
            # Phase 3: Memory Integration
            self._ctx.memory.remember(
                content=f"Task received: {task.description}", 
                role="user", 
                persist=True,
                metadata={"priority": task.priority, **task.metadata}
            )
            
            past_context = self._ctx.memory.search_long_term(task.description)
            if past_context:
                self.logger.info(f"Enriched context: found {len(past_context)} relevant past memories.")
            
            # Phase 2: Planning Subsystem
            plan: Plan = self.planner.create_plan(task)
            self.logger.info(f"Plan generated with {len(plan.steps)} steps.")
            
            self._ctx.memory.remember(
                content=f"Plan generated: {len(plan.steps)} steps for '{task.description}'", 
                role="assistant", 
                persist=False
            )
            
            return ExecutionResult(
                success=True,
                message=f"Task '{task.description}' planned successfully. Context enriched with {len(past_context)} memories. Awaiting execution phase.",
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