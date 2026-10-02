# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
GuardianGate — single choke point for tool dispatch.

Actual policy enforcement lives inside each tool (see policy.py docstring
for why). GuardianGate's job is narrower but still important:

1. It's the one place BrainEngine's Planner
   should call through, instead of reaching into
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

from datetime import datetime, timezone
from typing import Any

from loguru import logger

from glados.core.context import RuntimeContext
from glados.security.policy import PolicyViolation
from glados.tools.registry import ToolNotFoundError, ToolRegistry


# In-memory bounded ring buffer for audit logs (Web API requirement)
_audit_log_buffer: list[dict[str, Any]] = []
_MAX_BUFFER_SIZE = 1000


def get_guardian_logs(limit: int = 50) -> list[dict[str, Any]]:
    """
    Retrieves recent audit logs from the in-memory ring buffer.
    Used by the /api/v1/audit REST endpoint for the HEV-HUD tool console.
    """
    return _audit_log_buffer[-limit:] if _audit_log_buffer else []


def append_audit_log(entry: dict[str, Any]) -> None:
    """
    Appends an entry to the audit log buffer, maintaining bounded size.
    Should be called by GuardianGate on every allow/deny decision.
    """
    _audit_log_buffer.append(entry)
    if len(_audit_log_buffer) > _MAX_BUFFER_SIZE:
        _audit_log_buffer.pop(0)


class GuardianGate:
    """Wraps a ToolRegistry with structured audit logging around every call."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.logger = logger.bind(component="GuardianGate")

    def log_audit(self, action: str, status: str, details: str) -> None:
        """
        Record a generic audit entry in the ring buffer and log it.
        Useful for manual logging or external MCP client auditing.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "status": status,
            "details": details,
        }
        append_audit_log(entry)
        self.logger.info(f"[{status}] {action}: {details}")

    def recent_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Return the most recent audit entries from the ring buffer.
        Delegates to the module-level get_guardian_logs function.
        """
        return get_guardian_logs(limit)

    async def execute(self, name: str, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            tool = self.registry.get(name)
        except ToolNotFoundError:
            reason = "not_registered"
            self.logger.warning(f"guardian_deny tool={name} reason={reason}")
            append_audit_log({
                "timestamp": timestamp,
                "action": "TOOL_CALL",
                "status": "DENIED",
                "tool": name,
                "reason": reason,
            })
            raise

        try:
            result = await tool.execute(ctx, params)
        except PolicyViolation as e:
            reason = str(e)
            self.logger.warning(f"guardian_deny tool={name} reason={reason}")
            append_audit_log({
                "timestamp": timestamp,
                "action": "TOOL_CALL",
                "status": "DENIED",
                "tool": name,
                "reason": reason,
            })
            raise

        self.logger.info(f"guardian_allow tool={name}")
        append_audit_log({
            "timestamp": timestamp,
            "action": "TOOL_CALL",
            "status": "ALLOWED",
            "tool": name,
            "reason": "success",
        })
        return result