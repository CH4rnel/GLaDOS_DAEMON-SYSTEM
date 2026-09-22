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
    Coordinates memory retrieval, planning, tool execution, and result persistence.
    """

    def __init__(self, ctx: "RuntimeContext") -> None:
        self.ctx = ctx
        self.planner = Planner(ctx)
        self.logger = logger.bind(component="BrainEngine")
        self.logger.info("BrainEngine initialized")

    async def process_task(self, task_input: TaskInput) -> ExecutionResult:
        """
        Processes a task through the full cognitive pipeline.

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

            # 2. Create execution plan (pass context to avoid duplicate retrieval)
            plan = await self.planner.create_plan(task_input, context)
            self.logger.debug(f"Generated plan with {len(plan.steps)} step(s)")

            # 3. Execute plan steps
            execution_results: List[Dict[str, Any]] = []
            for step in plan.steps:
                self.logger.info(f"Executing step {step.step_number}: {step.action}")

                if step.tool_name and self.ctx.tools:
                    try:
                        step_result = await self.ctx.tools.execute(step.tool_name, step.parameters)
                        execution_results.append({
                            "step": step.step_number,
                            "tool": step.tool_name,
                            "result": step_result
                        })
                    except Exception as tool_error:
                        self.logger.error(f"Tool execution failed at step {step.step_number}: {tool_error}")
                        execution_results.append({
                            "step": step.step_number,
                            "tool": step.tool_name,
                            "error": str(tool_error)
                        })
                else:
                    self.logger.debug(f"Step {step.step_number} has no tool assigned, skipping execution.")

            result = ExecutionResult(
                success=True,
                message=f"Task completed: {task_input.description}",
                data={
                    "priority": task_input.priority,
                    "context_records_count": len(context),
                    "plan_steps_count": len(plan.steps),
                    "execution_results": execution_results
                }
            )

            # 4. Store result in memory
            self._persist_result(task_input, result)

            return result

        except Exception as e:
            self.logger.error(f"Task processing failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Task processing error: {str(e)}",
                data={}
            )

    def _persist_result(self, task_input: TaskInput, result: ExecutionResult) -> None:
        """Stores the task result in short-term memory for future context retrieval."""
        if not self.ctx.memory:
            self.logger.debug("Memory subsystem unavailable, skipping result persistence")
            return

        try:
            record = (
                f"Task: {task_input.description} | "
                f"Status: {'success' if result.success else 'failed'} | "
                f"Steps: {result.data.get('plan_steps_count', 0)}"
            )
            self.ctx.memory.add_short_term_record("brain", record)
            self.logger.debug("Task result persisted to short-term memory")
        except Exception as e:
            self.logger.error(f"Failed to persist task result: {e}")