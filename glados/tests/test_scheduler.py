# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock

from glados.core.context import RuntimeContext
from glados.autonomous.scheduler import Scheduler, ScheduledTask


class TestScheduler:
    def setup_method(self) -> None:
        self.ctx = MagicMock(spec=RuntimeContext)
        self.scheduler = Scheduler(ctx=self.ctx)

    def test_register_task_successfully(self) -> None:
        task = ScheduledTask(
            id="task_001",
            name="Test Task",
            cron_expression="* * * * *",
            callback=MagicMock()
        )
        self.scheduler.register_task(task)
        assert "task_001" in self.scheduler._tasks

    def test_register_duplicate_task_raises_error(self) -> None:
        task = ScheduledTask(
            id="task_001",
            name="Test Task",
            cron_expression="* * * * *",
            callback=MagicMock()
        )
        self.scheduler.register_task(task)
        with pytest.raises(ValueError, match="already registered"):
            self.scheduler.register_task(task)

    @pytest.mark.asyncio
    async def test_check_and_run_due_tasks_executes_callback(self) -> None:
        mock_callback = AsyncMock()
        task = ScheduledTask(
            id="task_002",
            name="Due Task",
            cron_expression="* * * * *",
            callback=mock_callback
        )
        task.next_run = datetime.now(timezone.utc) - timedelta(seconds=10)
        self.scheduler.register_task(task)

        await self.scheduler.check_and_run_due_tasks()

        mock_callback.assert_called_once()
        assert task.next_run > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_check_and_run_due_tasks_ignores_future_tasks(self) -> None:
        mock_callback = AsyncMock()
        task = ScheduledTask(
            id="task_003",
            name="Future Task",
            cron_expression="0 0 * * *",
            callback=mock_callback
        )
        task.next_run = datetime.now(timezone.utc) + timedelta(days=1)
        self.scheduler.register_task(task)

        await self.scheduler.check_and_run_due_tasks()

        mock_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_and_run_due_tasks_isolates_exceptions(self) -> None:
        def failing_callback() -> None:
            raise RuntimeError("Simulated failure")

        successful_callback = AsyncMock()

        failing_task = ScheduledTask(
            id="task_fail",
            name="Failing Task",
            cron_expression="* * * * *",
            callback=failing_callback
        )
        failing_task.next_run = datetime.now(timezone.utc) - timedelta(seconds=10)

        success_task = ScheduledTask(
            id="task_success",
            name="Successful Task",
            cron_expression="* * * * *",
            callback=successful_callback
        )
        success_task.next_run = datetime.now(timezone.utc) - timedelta(seconds=10)

        self.scheduler.register_task(failing_task)
        self.scheduler.register_task(success_task)

        await self.scheduler.check_and_run_due_tasks()

        successful_callback.assert_called_once()
        assert failing_task.next_run > datetime.now(timezone.utc)
        assert success_task.next_run > datetime.now(timezone.utc)