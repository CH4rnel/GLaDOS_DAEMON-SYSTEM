# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


async def rotate_logs(
    ctx: "RuntimeContext",
    log_file_path: str = "logs/glados.log",
    max_size_bytes: int = 10_000_000
) -> None:
    """
    Periodically checks log file size and rotates it if exceeds threshold.
    Renames current log to timestamped backup.
    """
    logger.debug("Initiating log rotation ritual...")
    
    log_file = Path(log_file_path)
    
    if not log_file.exists():
        logger.debug("Log file does not exist. Skipping rotation.")
        return
        
    try:
        file_size = log_file.stat().st_size
        
        if file_size > max_size_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
            backup_path = log_file.parent / backup_name
            
            log_file.rename(backup_path)
            logger.info(f"Log rotated: {log_file} -> {backup_path}")
        else:
            logger.debug(f"Log file size ({file_size} bytes) below threshold. No rotation needed.")
            
    except Exception as e:
        logger.error(f"Log rotation failed: {e}", exc_info=True)