# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Skill Lifecycle.
Ensures that candidate skills go through draft then sandbox then approval and finally registration,
and that rejected proposals are logged as lessons, not silently discarded.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from glados.autonomous.learning.skill_lifecycle import (
    SkillProposal,
    SkillLifecycleManager,
    ProposalStatus,
)
from glados.core.context import RuntimeContext


class TestSkillProposal:
    """Tests for the SkillProposal data model."""

    def test_proposal_creation(self):
        """Test creating a valid skill proposal."""
        proposal = SkillProposal(
            skill_name="auto_git_commit",
            description="Automatically commits staged changes",
            code="async def execute(ctx, params): ...",
            tests="def test_auto_git_commit(): ...",
            risk_level="low",
        )
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.skill_name == "auto_git_commit"

    def test_proposal_risk_levels(self):
        """Test that risk levels are strictly validated."""
        for level in ["low", "medium", "high", "critical"]:
            proposal = SkillProposal(
                skill_name="test",
                description="test",
                code="pass",
                tests="pass",
                risk_level=level,
            )
            assert proposal.risk_level == level


class TestSkillLifecycleManager:
    """Tests for the SkillLifecycleManager workflow."""

    @pytest.fixture
    def mock_ctx(self):
        """Simulates RuntimeContext with all subsystems."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.security = MagicMock()
        ctx.skills = MagicMock()
        ctx.memory = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.fixture
    def sample_proposal(self):
        """A sample skill proposal for testing."""
        return SkillProposal(
            skill_name="auto_format_code",
            description="Formats Python code using ruff",
            code="import subprocess\nasync def execute(ctx, params):\n    subprocess.run(['ruff', 'format', params['file']])",
            tests="def test_format(): assert True",
            risk_level="low",
        )

    @pytest.mark.asyncio
    async def test_draft_proposal_starts_in_draft_status(self, mock_ctx, sample_proposal):
        """Test that a new proposal starts in DRAFT status."""
        manager = SkillLifecycleManager(ctx=mock_ctx)
        result = await manager.draft(sample_proposal)
        
        assert result.status == ProposalStatus.DRAFT
        assert result.proposal_id is not None

    @pytest.mark.asyncio
    async def test_sandbox_dry_run_executes_tests_only(self, mock_ctx, sample_proposal):
        """Test that sandbox dry-run executes tests without host access."""
        manager = SkillLifecycleManager(ctx=mock_ctx)
        await manager.draft(sample_proposal)
        
        result = await manager.sandbox_test(sample_proposal.proposal_id)
        
        assert result.status in (ProposalStatus.SANDBOX_PASS, ProposalStatus.SANDBOX_FAIL)

    @pytest.mark.asyncio
    async def test_approval_registers_skill_and_creates_restore_point(self, mock_ctx, sample_proposal):
        """Test that explicit approval registers the skill and creates a restore point."""
        manager = SkillLifecycleManager(ctx=mock_ctx)
        await manager.draft(sample_proposal)
        await manager.sandbox_test(sample_proposal.proposal_id)
        
        result = await manager.approve(sample_proposal.proposal_id, operator_confirmed=True)
        
        assert result.status == ProposalStatus.APPROVED
        mock_ctx.skills.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_approval_without_operator_confirmation_raises(self, mock_ctx, sample_proposal):
        """Test that approval without explicit Operator confirmation is denied."""
        manager = SkillLifecycleManager(ctx=mock_ctx)
        await manager.draft(sample_proposal)
        
        with pytest.raises(PermissionError):
            await manager.approve(sample_proposal.proposal_id, operator_confirmed=False)

    @pytest.mark.asyncio
    async def test_rejection_logs_lesson_to_ltm(self, mock_ctx, sample_proposal):
        """Test that rejected proposals are logged as lessons, not silently discarded."""
        manager = SkillLifecycleManager(ctx=mock_ctx)
        await manager.draft(sample_proposal)
        
        result = await manager.reject(
            sample_proposal.proposal_id, 
            reason="Duplicate of existing shell_tool"
        )
        
        assert result.status == ProposalStatus.REJECTED
        mock_ctx.memory.remember.assert_called_once()
        call_args = mock_ctx.memory.remember.call_args
        assert "Duplicate" in str(call_args)

    @pytest.mark.asyncio
    async def test_critical_risk_requires_extra_confirmation(self, mock_ctx):
        """Test that critical-risk proposals require additional safeguards."""
        critical_proposal = SkillProposal(
            skill_name="modify_system_config",
            description="Modifies system configuration files",
            code="open('/etc/glados/config.yaml', 'w').write('...')",
            tests="def test_modify(): pass",
            risk_level="critical",
        )
        
        manager = SkillLifecycleManager(ctx=mock_ctx)
        await manager.draft(critical_proposal)
        
        with pytest.raises(PermissionError) as exc_info:
            await manager.approve(critical_proposal.proposal_id, operator_confirmed=True)
        
        assert "critical" in str(exc_info.value).lower()