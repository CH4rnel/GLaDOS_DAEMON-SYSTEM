# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

from __future__ import annotations

from typing import TYPE_CHECKING, List

from glados.autonomous.scheduler import ScheduledTask
from glados.autonomous.tasks.memory_tasks import consolidate_memory
from glados.autonomous.tasks.monitoring_tasks import monitor_system_resources
from glados.autonomous.tasks.log_rotation_tasks import rotate_logs

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

    # System Resource Monitoring Task
    async def _monitoring_callback() -> None:
        await monitor_system_resources(ctx)

    tasks.append(
        ScheduledTask(
            id="system_monitoring",
            name="System Resource Monitoring",
            cron_expression="*/2 * * * *",
            callback=_monitoring_callback
        )
    )

    # Log Rotation Task
    async def _log_rotation_callback() -> None:
        await rotate_logs(ctx)

    tasks.append(
        ScheduledTask(
            id="log_rotation",
            name="Log Rotation",
            cron_expression="0 * * * *",
            callback=_log_rotation_callback
        )
    )

    return tasks