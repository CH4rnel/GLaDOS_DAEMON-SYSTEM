# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict

from croniter import croniter
from loguru import logger

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


@dataclass
class ScheduledTask:
    id: str
    name: str
    cron_expression: str
    callback: Callable[[], Any]
    next_run: datetime = field(init=False)

    def __post_init__(self) -> None:
        self._update_next_run()

    def _update_next_run(self) -> None:
        base_time = getattr(self, "next_run", None) or datetime.now(timezone.utc)
        cron = croniter(self.cron_expression, base_time)
        self.next_run = cron.get_next(datetime)

    def update_next_run(self) -> None:
        self._update_next_run()


class Scheduler:
    def __init__(self, ctx: "RuntimeContext") -> None:
        self.ctx = ctx
        self.logger = logger.bind(component="Scheduler")
        self._tasks: Dict[str, ScheduledTask] = {}
        self.logger.debug("Scheduler initialized")

    def register_task(self, task: ScheduledTask) -> None:
        if task.id in self._tasks:
            raise ValueError(f"Task with id '{task.id}' is already registered.")
        self._tasks[task.id] = task
        self.logger.debug(f"Registered task: {task.name} ({task.id})")

    async def check_and_run_due_tasks(self) -> None:
        now = datetime.now(timezone.utc)
        due_tasks = [task for task in self._tasks.values() if task.next_run <= now]

        for task in due_tasks:
            try:
                self.logger.debug(f"Executing scheduled task: {task.name} ({task.id})")
                if inspect.iscoroutinefunction(task.callback):
                    await task.callback()
                else:
                    task.callback()
                
                task.update_next_run()
                self.logger.debug(f"Task {task.id} rescheduled for {task.next_run}")
            except Exception as e:
                self.logger.error(f"Task {task.id} failed during execution: {e}", exc_info=True)
                task.update_next_run()