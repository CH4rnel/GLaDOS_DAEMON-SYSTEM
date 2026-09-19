# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


async def consolidate_memory(ctx: "RuntimeContext") -> None:
    """
    Periodically flushes short-term memory records into long-term storage.
    This ensures critical context is preserved across daemon restarts.
    """
    logger.debug("Initiating memory consolidation ritual...")
    
    if not ctx.memory:
        logger.warning("Memory subsystem not available. Skipping consolidation.")
        return
        
    try:
        await ctx.memory.consolidate()
        logger.debug("Memory consolidation completed successfully.")
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}", exc_info=True)