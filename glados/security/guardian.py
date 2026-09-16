# glados/security/guardian.py
# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
GuardianGate — single choke point for tool dispatch.

Actual policy enforcement lives inside each tool (see policy.py docstring
for why). GuardianGate's job is narrower but still important:

1. It's the one place BrainEngine's Planner (Phase 7 — currently a TODO in
   brain/engine.py) should call through, instead of reaching into
   ToolRegistry directly. That gives future-us a single point to extend
   with rate limiting, per-task budgets, or a human-approval hook, without
   touching every tool.
2. It writes a structured allow/deny audit line for every attempted call,
   independent of whatever a tool's own logging does — useful for forensics
   if a tool's internal logging is ever bypassed or tampered with.

This does NOT replace the in-tool checks — it's a second, independent log
of the same decision, not the decision itself.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from glados.core.context import RuntimeContext
from glados.security.policy import PolicyViolation
from glados.tools.registry import ToolNotFoundError, ToolRegistry


class GuardianGate:
    """Wraps a ToolRegistry with structured audit logging around every call."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.logger = logger.bind(component="GuardianGate")

    async def execute(self, name: str, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        try:
            tool = self.registry.get(name)
        except ToolNotFoundError:
            self.logger.warning(f"guardian_deny tool={name} reason=not_registered")
            raise

        try:
            result = await tool.execute(ctx, params)
        except PolicyViolation as e:
            self.logger.warning(f"guardian_deny tool={name} reason={e}")
            raise

        self.logger.info(f"guardian_allow tool={name}")
        return result