# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING, List

from loguru import logger

from glados.core.event import Event, EventPriority

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext
    from glados.autonomous.events import EventHandler


async def run_system_diagnostics(ctx: "RuntimeContext", event_handler: "EventHandler") -> None:
    """
    Periodically checks availability of critical subsystems.
    Records success in memory or publishes failure event.
    """
    logger.debug("Initiating system self-diagnostics ritual...")
    
    failed_components: List[str] = []
    
    if not ctx.memory:
        failed_components.append("Memory")
    if not getattr(ctx, "llm_registry", None):
        failed_components.append("LLM Registry")
    if not getattr(ctx, "tools", None):
        failed_components.append("Tools")
    
    if failed_components:
        logger.warning(f"System diagnostics failed: {failed_components}")
        failure_event = Event(
            type="system.health_check.failed",
            priority=EventPriority.HIGH,
            payload={"failed_components": failed_components}
        )
        event_handler.publish(failure_event)
    else:
        logger.debug("System diagnostics passed. All critical subsystems operational.")
        if ctx.memory:
            ctx.memory.add_short_term_record("system", "Self-diagnostics passed successfully")