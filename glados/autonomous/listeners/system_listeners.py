# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from glados.core.event import Event

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


def create_system_boot_listener(ctx: "RuntimeContext"):
    """
    Factory function that creates an asynchronous listener for the system.boot event.
    Uses a closure to maintain access to the RuntimeContext.
    """
    
    async def on_system_boot(event: Event) -> None:
        logger.info(f"System boot event received: {event.payload}")
        
        if ctx.memory:
            record_content = f"Daemon awakened. Boot status: {event.payload.get('status', 'unknown')}"
            ctx.memory.add_short_term_record("system", record_content)
            logger.debug("Boot sequence recorded in short-term memory.")
        else:
            logger.warning("Memory subsystem unavailable. Boot sequence not recorded.")

    return on_system_boot