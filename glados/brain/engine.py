# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Brain Engine module for GLaDOS_DAEMON-SYSTEM.
Responsible for orchestrating task processing, planning, and execution.
"""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext
from glados.brain.models import TaskInput, ExecutionResult
from glados.brain.planner import Planner, Plan
from glados.llm.models import LLMMessage
from glados.llm.router import RoutingStrategy


class BrainEngine:
    """
    Central orchestrator of the GLaDOS system.
    Manages the task processing lifecycle: from receiving to planning and execution.
    """

    def __init__(self, ctx: RuntimeContext) -> None:
        """
        Initializes the BrainEngine using dependency injection.
        
        :param ctx: Global execution context containing Identity, Logger, Memory, and LLMRouter.
        """
        self._ctx = ctx
        self.logger = ctx.logger.bind(component="BrainEngine")
        
        # Initialize Phase 2 subsystems
        self.planner = Planner()
        
        self.logger.debug("BrainEngine initialized successfully with Planner and LLMRouter access.")

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
            # Memory Integration
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
            # Phase 6: LLM-Powered Planning
            # ---------------------------------------------------------
            # 3. Try to use LLMRouter for planning if available
            plan = await self._plan_with_llm(task, past_context)
            
            if plan is None:
                # Fallback to mock planner
                self.logger.warning("LLM planning unavailable, falling back to mock planner")
                plan = self.planner.create_plan(task)
            
            self.logger.info(f"Plan generated with {len(plan.steps)} steps.")
            
            # 4. Remember the generated plan in short-term memory (transient state)
            self._ctx.memory.remember(
                content=f"Plan generated: {len(plan.steps)} steps for '{task.description}'", 
                role="assistant", 
                persist=False
            )
            
            # ---------------------------------------------------------
            # TODO !Execute skills and tools based on the plan!
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
                    "memories_found": len(past_context),
                    "llm_used": plan is not None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process task: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Internal BrainEngine error: {str(e)}",
                data={"error_type": type(e).__name__}
            )

    async def _plan_with_llm(
        self, 
        task: TaskInput, 
        past_context: list
    ) -> Plan | None:
        """
        Attempt to generate a plan using LLMRouter.
        
        :param task: The task to plan.
        :param past_context: Relevant past memories.
        :return: Generated Plan or None if LLM is unavailable.
        """
        # Check if LLMRouter is available
        if not self._ctx.llm_router:
            return None
        
        # Check if there are any active agents
        active_agents = self._ctx.llm_agents.get_active() if self._ctx.llm_agents else []
        if not active_agents:
            return None
        
        try:
            # Build messages for LLM
            messages = self._build_planning_messages(task, past_context)
            
            # Determine routing strategy
            strategy = RoutingStrategy.SINGLE
            agent_id = task.metadata.get("preferred_agent")
            tag = task.metadata.get("preferred_tag")
            
            # Route to LLM
            if agent_id:
                response = await self._ctx.llm_router.route(
                    messages=messages,
                    strategy=strategy,
                    agent_id=agent_id
                )
            elif tag:
                response = await self._ctx.llm_router.route(
                    messages=messages,
                    strategy=strategy,
                    tag=tag
                )
            else:
                # Use first active agent
                response = await self._ctx.llm_router.route(
                    messages=messages,
                    strategy=strategy,
                    agent_id=active_agents[0].agent_id
                )
            
            # Parse LLM response into Plan
            if response and not response.is_error:
                plan = self._parse_llm_plan(response.content, task)
                return plan
            
            return None
            
        except Exception as e:
            self.logger.warning(f"LLM planning failed: {e}")
            return None

    def _build_planning_messages(
        self, 
        task: TaskInput, 
        past_context: list
    ) -> list[LLMMessage]:
        """
        Build messages for LLM planning request.
        
        :param task: The task to plan.
        :param past_context: Relevant past memories.
        :return: List of LLMMessage objects.
        """
        messages = []
        
        # Add past context if available
        if past_context:
            context_text = "\n".join([
                f"[{mem.role}] {mem.content}" 
                for mem in past_context[-5:]  # Last 5 memories
            ])
            messages.append(LLMMessage(
                role="system",
                content=f"Relevant past context:\n{context_text}"
            ))
        
        # Add task description
        messages.append(LLMMessage(
            role="user",
            content=f"Create a step-by-step plan for this task: {task.description}"
        ))
        
        return messages

    def _parse_llm_plan(self, llm_response: str, task: TaskInput) -> Plan:
        """
        Parse LLM response into a Plan object.
        Currently uses simple parsing. Future: Use structured output.
        
        :param llm_response: Raw LLM response text.
        :param task: Original task.
        :return: Parsed Plan object.
        """
        # Simple parsing: split by lines and create steps
        lines = [line.strip() for line in llm_response.split('\n') if line.strip()]
        
        steps = []
        for i, line in enumerate(lines, 1):
            # Remove common prefixes like "Step 1:", "1.", etc.
            clean_line = line
            for prefix in ["Step", "step", f"{i}.", f"{i})"]:
                if clean_line.startswith(prefix):
                    clean_line = clean_line[len(prefix):].strip(":").strip()
                    break
            
            if clean_line:
                from glados.brain.planner import PlanStep
                steps.append(PlanStep(
                    step_id=i,
                    action="execute",
                    description=clean_line
                ))
        
        # If parsing failed, create a simple plan
        if not steps:
            steps = [
                PlanStep(step_id=1, action="analyze", description=llm_response[:100])
            ]
        
        return Plan(
            task_description=task.description,
            steps=steps
        )