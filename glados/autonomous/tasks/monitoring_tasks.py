# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING

import psutil
from loguru import logger

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


async def monitor_system_resources(ctx: "RuntimeContext") -> None:
    """
    Periodically collects system resource metrics (CPU, RAM, Disk)
    and records them in short-term memory for historical analysis.
    """
    logger.debug("Initiating system resource monitoring ritual...")
    
    if not ctx.memory:
        logger.warning("Memory subsystem not available. Skipping resource monitoring.")
        return
        
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        metrics_record = (
            f"System Resources - CPU: {cpu_percent}%, "
            f"RAM: {ram_percent}%, "
            f"Disk: {disk_percent}%"
        )
        
        ctx.memory.add_short_term_record("system", metrics_record)
        logger.debug(f"System resources recorded: {metrics_record}")
        
    except Exception as e:
        logger.error(f"System resource monitoring failed: {e}", exc_info=True)