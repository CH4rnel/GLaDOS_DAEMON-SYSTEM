# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any, Dict, List

from croniter import croniter

@dataclass
class ScheduledTask:
    """It represents a single scheduled task."""
    id: str
    name: str
    cron_expression: str
    callback: Callable[[], Any]
    next_run: datetime = field(init=False)
    
    def __post_init__(self) -> None:
        self._update_next_run()

    def _update_next_run(self) -> None:
        # If `next_run` is already set, we use it as the basis for calculating the next interval.
        # This prevents "getting stuck" on a single minute when running tests quickly.
        # and ensures the correct offset relative to the cron schedule in production.
        base_time = getattr(self, 'next_run', None) or datetime.now()
        cron = croniter(self.cron_expression, base_time)
        self.next_run = cron.get_next(datetime)

    def update_next_run(self) -> None:
        """Updates the next execution time after completion."""
        self._update_next_run()


class Scheduler:
    """Manages the registration and timestamps of task execution."""
    
    def __init__(self) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}

    def register(self, task: ScheduledTask) -> None:
        if task.id in self._tasks:
            raise ValueError(f"Task with id '{task.id}' already registered.")
        self._tasks[task.id] = task

    def get_tasks(self) -> List[ScheduledTask]:
        return list(self._tasks.values())

    def get_due_tasks(self) -> List[ScheduledTask]:
        """Returns a list of tasks that are ready for execution right now."""
        now = datetime.now()
        due_tasks = []
        for task in self._tasks.values():
            if task.next_run <= now:
                due_tasks.append(task)
        return due_tasks
        
    def mark_executed(self, task_id: str) -> None:
        """Updates the task schedule after its execution."""
        if task_id in self._tasks:
            self._tasks[task_id].update_next_run()