# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Tests for the GLaDOS Brain Planner subsystem.
Follows TDD methodology to define the contract before implementation.
"""

import pytest
from pydantic import ValidationError

# These imports will fail initially (Red Phase) until we implement the module
from glados.brain.planner import Planner, Plan, PlanStep
from glados.brain.engine import TaskInput


class TestPlanModels:
    """Tests for Pydantic data models used in planning."""

    def test_plan_step_creation_valid(self):
        """Test creating a valid PlanStep."""
        step = PlanStep(step_id=1, action="analyze", description="Analyze system logs")
        assert step.step_id == 1
        assert step.action == "analyze"
        assert step.status == "pending"  # Default value

    def test_plan_step_creation_invalid_status(self):
        """Test that invalid status raises ValidationError."""
        with pytest.raises(ValidationError):
            PlanStep(step_id=1, action="analyze", description="Test", status="invalid_status")

    def test_plan_creation_valid(self):
        """Test creating a valid Plan with multiple steps."""
        steps = [
            PlanStep(step_id=1, action="read", description="Read config"),
            PlanStep(step_id=2, action="execute", description="Run script")
        ]
        plan = Plan(task_description="Update system", steps=steps)
        assert len(plan.steps) == 2
        assert plan.task_description == "Update system"


class TestPlanner:
    """Tests for the core Planner logic."""

    def test_planner_initialization(self):
        """Test that Planner can be initialized."""
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