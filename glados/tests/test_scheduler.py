# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

import pytest
from datetime import datetime, timedelta

# Importing what we implement (TDD Red/Green)
from glados.core.scheduler import Scheduler, ScheduledTask

def dummy_callback() -> None:
    pass

@pytest.fixture
def scheduler() -> Scheduler:
    return Scheduler()

@pytest.fixture
def sample_task() -> ScheduledTask:
    # Task performed every minute
    return ScheduledTask(
        id="task_001",
        name="System Health Check",
        cron_expression="* * * * *",
        callback=dummy_callback
    )

class TestScheduler:
    def test_register_task_successfully(self, scheduler: Scheduler, sample_task: ScheduledTask) -> None:
        scheduler.register(sample_task)
        tasks = scheduler.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == "task_001"

    def test_register_duplicate_task_raises_error(self, scheduler: Scheduler, sample_task: ScheduledTask) -> None:
        scheduler.register(sample_task)
        with pytest.raises(ValueError, match="already registered"):
            scheduler.register(sample_task)

    def test_next_run_is_calculated_on_init(self, sample_task: ScheduledTask) -> None:
        # The next launch is scheduled for the future.
        assert sample_task.next_run > datetime.now()

    def test_get_due_tasks_returns_empty_when_not_due(self, scheduler: Scheduler, sample_task: ScheduledTask) -> None:
        scheduler.register(sample_task)
        # Since next_run is in the future, no task should be ready for execution right now.
        due = scheduler.get_due_tasks()
        assert len(due) == 0

    def test_get_due_tasks_returns_task_when_due(self, scheduler: Scheduler, sample_task: ScheduledTask) -> None:
        scheduler.register(sample_task)
        # We artificially shift the time of the next execution to the past to test the trigger.
        sample_task.next_run = datetime.now() - timedelta(seconds=10)
        
        due = scheduler.get_due_tasks()
        assert len(due) == 1
        assert due[0].id == "task_001"

    def test_mark_executed_updates_next_run(self, scheduler: Scheduler, sample_task: ScheduledTask) -> None:
        scheduler.register(sample_task)
        old_next_run = sample_task.next_run
        
        # Simulating task execution
        scheduler.mark_executed("task_001")
        
        # The next launch time must be updated to a value greater than the previous one.
        assert sample_task.next_run > old_next_run