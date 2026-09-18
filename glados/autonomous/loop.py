# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Autonomous Loop for GLaDOS_DAEMON-SYSTEM.
Central runtime loop that executes periodically and coordinates scheduler and event handler.
"""
from datetime import datetime, timezone
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger

from glados.core.context import RuntimeContext

if TYPE_CHECKING:
    from glados.autonomous.scheduler import Scheduler
    from glados.autonomous.events import EventHandler


class AutonomousLoop:
    """
    Central autonomous runtime loop.
    Executes periodically, checking for scheduled tasks and processing events.
    """

    def __init__(
        self,
        ctx: RuntimeContext,
        scheduler: "Scheduler",
        event_handler: "EventHandler",
        interval_seconds: int = 60
    ) -> None:
        """
        Initialize the autonomous loop.
        
        :param ctx: Runtime context with all dependencies
        :param scheduler: Scheduler for periodic tasks
        :param event_handler: Event handler for processing events
        :param interval_seconds: Interval between iterations (default 60s)
        """
        self.ctx = ctx
        self.scheduler = scheduler
        self.event_handler = event_handler
        self.interval_seconds = interval_seconds
        
        self._running = False
        self._last_iteration: datetime | None = None
        self._iteration_count = 0
        
        self.logger = logger.bind(component="AutonomousLoop")
        self.logger.info(
            f"AutonomousLoop initialized with interval={interval_seconds}s"
        )

    async def run_once(self) -> None:
        """
        Execute a single iteration of the loop.
        Useful for testing or manual triggering.
        """
        await self._run_iteration()

    async def run_continuous(self, max_iterations: int | None = None) -> None:
        """
        Run the loop continuously until stopped or max_iterations reached.
        
        :param max_iterations: Maximum number of iterations (None = unlimited)
        """
        self._running = True
        self.logger.info("AutonomousLoop started in continuous mode")
        
        iteration = 0
        try:
            while self._running:
                await self._run_iteration()
                iteration += 1
                
                if max_iterations and iteration >= max_iterations:
                    self.logger.info(f"Reached max iterations: {max_iterations}")
                    break
                
                # Sleep until next iteration
                await asyncio.sleep(self.interval_seconds)
                
        except asyncio.CancelledError:
            self.logger.info("AutonomousLoop cancelled")
        except Exception as e:
            self.logger.error(f"AutonomousLoop fatal error: {e}", exc_info=True)
        finally:
            self._running = False
            self.logger.info("AutonomousLoop stopped")

    def stop(self) -> None:
        """
        Gracefully stop the loop.
        The loop will finish current iteration and then stop.
        """
        self.logger.info("AutonomousLoop stop requested")
        self._running = False

    async def _run_iteration(self) -> None:
        """
        Execute a single iteration of the loop.
        Calls scheduler and event handler, handles exceptions gracefully.
        """
        self._last_iteration = datetime.now(timezone.utc)
        self._iteration_count += 1
        
        self.logger.debug(
            f"AutonomousLoop iteration #{self._iteration_count} started"
        )
        
        try:
            # 1. Check and run scheduled tasks
            await self.scheduler.check_and_run_due_tasks()
            
            # 2. Process pending events
            await self.event_handler.process_pending_events()
            
            self.logger.debug(
                f"AutonomousLoop iteration #{self._iteration_count} completed"
            )
            
        except Exception as e:
            # Log error but don't stop the loop
            self.logger.error(
                f"AutonomousLoop iteration #{self._iteration_count} failed: {e}",
                exc_info=True
            )

    def status(self) -> dict:
        """
        Get current status of the autonomous loop.
        
        :return: Dictionary with status information
        """
        return {
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "iteration_count": self._iteration_count,
            "last_iteration": self._last_iteration.isoformat() if self._last_iteration else None
        }