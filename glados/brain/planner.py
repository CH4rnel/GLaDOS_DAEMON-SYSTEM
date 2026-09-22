# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List

from loguru import logger

from glados.brain.models import TaskInput

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


PLANNER_SYSTEM_PROMPT = """You are GLaDOS Planner, a cognitive subsystem that decomposes tasks into executable steps.

You MUST respond with valid JSON only, following this exact schema:
{
  "steps": [
    {
      "action": "Brief description of what this step does",
      "tool_name": "name_of_tool_to_use_or_null",
      "parameters": {}
    }
  ]
}

Available tools: system_info, shell_exec, file_read, file_write, file_delete, file_list, git_status, python_exec.
Use tool_name=null for reasoning-only steps.
Do NOT include any text outside the JSON object."""


@dataclass
class PlanStep:
    """Represents a single step in an execution plan."""
    step_number: int
    action: str
    tool_name: str | None = None
    parameters: dict = field(default_factory=dict)


@dataclass
class Plan:
    """Represents a structured execution plan for a task."""
    task_description: str
    steps: List[PlanStep] = field(default_factory=list)

    def add_step(self, action: str, tool_name: str | None = None, parameters: dict | None = None) -> None:
        """Adds a new step to the plan."""
        step_number = len(self.steps) + 1
        step = PlanStep(
            step_number=step_number,
            action=action,
            tool_name=tool_name,
            parameters=parameters or {}
        )
        self.steps.append(step)


class Planner:
    """
    Generates structured execution plans from task descriptions.
    Uses LLM for intelligent planning with automatic fallback to rule-based logic.
    """

    def __init__(self, ctx: "RuntimeContext") -> None:
        self.ctx = ctx
        self.logger = logger.bind(component="Planner")
        self.logger.info("Planner initialized")

    async def create_plan(self, task_input: TaskInput, context: List[Dict[str, Any]] | None = None) -> Plan:
        """
        Creates an execution plan for the given task.
        Attempts LLM-based planning first, falls back to rule-based on failure.
        
        :param task_input: Task description and metadata
        :param context: Optional context from memory to inform planning
        :return: Structured execution plan
        :raises ValueError: If task description is empty
        """
        if not task_input.description or not task_input.description.strip():
            raise ValueError("Task description cannot be empty")

        self.logger.info(f"Creating plan for task: {task_input.description}")

        # Attempt LLM-based planning
        if self.ctx.llm_router:
            try:
                plan = await self._create_plan_with_llm(task_input, context or [])
                if plan and len(plan.steps) > 0:
                    self.logger.debug(f"LLM-generated plan with {len(plan.steps)} step(s)")
                    return plan
            except Exception as e:
                self.logger.warning(f"LLM planning failed, falling back to rule-based: {e}")

        # Fallback to rule-based planning
        return self._create_rule_based_plan(task_input)

    async def _create_plan_with_llm(self, task_input: TaskInput, context: List[Dict[str, Any]]) -> Plan | None:
        """Attempts to generate a plan using the LLM router."""
        user_prompt = self._build_user_prompt(task_input, context)
        
        llm_response = await self.ctx.llm_router.generate(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        return self._parse_llm_response(task_input.description, llm_response)

    def _build_user_prompt(self, task_input: TaskInput, context: List[Dict[str, Any]]) -> str:
        """Builds the user prompt with task description and optional context."""
        prompt_parts = [f"Task: {task_input.description}"]
        
        if context:
            prompt_parts.append("\nRecent context:")
            for record in context[-5:]:
                role = record.get("role", "unknown")
                content = record.get("content", "")
                prompt_parts.append(f"[{role}]: {content}")
        
        prompt_parts.append("\nGenerate a step-by-step execution plan as JSON.")
        return "\n".join(prompt_parts)

    def _parse_llm_response(self, task_description: str, response: str) -> Plan | None:
        """Parses LLM JSON response into a Plan object."""
        try:
            # Extract JSON from response (handle potential markdown code blocks)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
            
            data = json.loads(cleaned)
            
            if "steps" not in data or not isinstance(data["steps"], list):
                self.logger.warning("LLM response missing 'steps' key")
                return None
            
            plan = Plan(task_description=task_description)
            for idx, step_data in enumerate(data["steps"], start=1):
                if not isinstance(step_data, dict):
                    continue
                plan.steps.append(PlanStep(
                    step_number=idx,
                    action=step_data.get("action", f"Step {idx}"),
                    tool_name=step_data.get("tool_name"),
                    parameters=step_data.get("parameters") or {}
                ))
            
            return plan if plan.steps else None
            
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            self.logger.warning(f"Failed to parse LLM plan response: {e}")
            return None

    def _create_rule_based_plan(self, task_input: TaskInput) -> Plan:
        """Fallback rule-based plan generation."""
        self.logger.debug("Using rule-based fallback planning")
        plan = Plan(task_description=task_input.description)
        plan.add_step(
            action=f"Process task: {task_input.description}",
            tool_name=None,
            parameters={"priority": task_input.priority}
        )
        return plan