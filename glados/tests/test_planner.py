# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS Brain Planner subsystem.
Follows TDD methodology to define the contract before implementation.
"""

import pytest
from pydantic import ValidationError

# Corrected imports after resolving circular dependency
from glados.brain.models import TaskInput
from glados.brain.planner import Planner, Plan, PlanStep


class TestPlanStep:
    """Tests for the PlanStep Pydantic model."""

    def test_plan_step_creation_valid(self):
        """Test creating a valid PlanStep with default status."""
        step = PlanStep(step_id=1, action="analyze", description="Analyze system logs")
        assert step.step_id == 1
        assert step.action == "analyze"
        assert step.description == "Analyze system logs"
        assert step.status == "pending"  # Default value

    def test_plan_step_with_explicit_status(self):
        """Test creating a PlanStep with an explicit status."""
        step = PlanStep(step_id=2, action="execute", description="Run script", status="completed")
        assert step.status == "completed"

    def test_plan_step_invalid_status(self):
        """Test that invalid status raises ValidationError."""
        with pytest.raises(ValidationError):
            PlanStep(step_id=1, action="analyze", description="Test", status="invalid_status")

    def test_plan_step_invalid_step_id(self):
        """Test that step_id < 1 raises ValidationError."""
        with pytest.raises(ValidationError):
            PlanStep(step_id=0, action="analyze", description="Test")

    def test_plan_step_empty_action_rejected(self):
        """Test that empty action is rejected."""
        with pytest.raises(ValidationError):
            PlanStep(step_id=1, action="", description="Test")

    def test_plan_step_empty_description_rejected(self):
        """Test that empty description is rejected."""
        with pytest.raises(ValidationError):
            PlanStep(step_id=1, action="analyze", description="")


class TestPlan:
    """Tests for the Plan Pydantic model."""

    def test_plan_creation_valid(self):
        """Test creating a valid Plan with multiple steps."""
        steps = [
            PlanStep(step_id=1, action="read", description="Read config"),
            PlanStep(step_id=2, action="execute", description="Run script")
        ]
        plan = Plan(task_description="Update system", steps=steps)
        assert len(plan.steps) == 2
        assert plan.task_description == "Update system"

    def test_plan_creation_empty_steps(self):
        """Test creating a Plan with no steps (edge case)."""
        plan = Plan(task_description="Empty task", steps=[])
        assert len(plan.steps) == 0

    def test_plan_creation_default_steps(self):
        """Test that Plan can be created without explicitly providing steps."""
        plan = Plan(task_description="Default steps")
        assert plan.steps == []

    def test_plan_empty_description_rejected(self):
        """Test that empty task_description is rejected."""
        with pytest.raises(ValidationError):
            Plan(task_description="", steps=[])


class TestPlanner:
    """Tests for the core Planner logic."""

    def test_planner_initialization(self):
        """Test that Planner can be initialized without errors."""
        planner = Planner()
        assert planner is not None

    def test_create_plan_returns_plan_object(self):
        """Test that create_plan returns a valid Plan object."""
        planner = Planner()
        task = TaskInput(description="Check disk space", priority=2)
        
        plan = planner.create_plan(task)
        
        assert isinstance(plan, Plan)
        assert plan.task_description == "Check disk space"
        assert len(plan.steps) > 0
        assert all(isinstance(step, PlanStep) for step in plan.steps)

    def test_create_plan_generates_multiple_steps(self):
        """Test that the planner generates at least 3 steps (analyze, execute, verify)."""
        planner = Planner()
        task = TaskInput(description="Test task")
        
        plan = planner.create_plan(task)
        
        assert len(plan.steps) >= 3
        actions = [step.action for step in plan.steps]
        assert "analyze" in actions
        assert "execute" in actions
        assert "verify" in actions

    def test_create_plan_preserves_task_description(self):
        """Test that the plan preserves the original task description."""
        planner = Planner()
        task = TaskInput(description="Complex multi-step operation")
        
        plan = planner.create_plan(task)
        
        assert plan.task_description == "Complex multi-step operation"

    def test_create_plan_steps_have_unique_ids(self):
        """Test that all generated steps have unique step_ids."""
        planner = Planner()
        task = TaskInput(description="Test uniqueness")
        
        plan = planner.create_plan(task)
        
        step_ids = [step.step_id for step in plan.steps]
        assert len(step_ids) == len(set(step_ids)), "Step IDs must be unique"

    def test_create_plan_steps_have_descriptions(self):
        """Test that all generated steps have non-empty descriptions."""
        planner = Planner()
        task = TaskInput(description="Test descriptions")
        
        plan = planner.create_plan(task)
        
        for step in plan.steps:
            assert len(step.description) > 0
            assert step.action in step.description.lower() or task.description.lower() in step.description.lower()

    def test_create_plan_all_steps_initially_pending(self):
        """Test that all generated steps have status 'pending' initially."""
        planner = Planner()
        task = TaskInput(description="Test initial status")
        
        plan = planner.create_plan(task)
        
        for step in plan.steps:
            assert step.status == "pending"

    def test_create_plan_with_metadata(self):
        """Test that Planner handles TaskInput with metadata correctly."""
        planner = Planner()
        task = TaskInput(
            description="Task with metadata",
            priority=3,
            metadata={"source": "cli", "session_id": "abc123"}
        )
        
        plan = planner.create_plan(task)
        
        assert isinstance(plan, Plan)
        assert plan.task_description == "Task with metadata"