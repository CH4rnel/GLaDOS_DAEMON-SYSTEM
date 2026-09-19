# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING, List

from glados.autonomous.scheduler import ScheduledTask
from glados.autonomous.tasks.memory_tasks import consolidate_memory

if TYPE_CHECKING:
    from glados.core.context import RuntimeContext


def create_default_tasks(ctx: "RuntimeContext") -> List[ScheduledTask]:
    """
    Generates the standard set of background tasks for the autonomous daemon.
    """
    tasks = []

    # Memory Consolidation Task
    async def _consolidation_callback() -> None:
        await consolidate_memory(ctx)

    tasks.append(
        ScheduledTask(
            id="memory_consolidation",
            name="Memory Consolidation",
            cron_expression="*/5 * * * *",
            callback=_consolidation_callback
        )
    )

    return tasks