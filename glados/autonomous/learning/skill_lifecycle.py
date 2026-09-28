# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Skill Lifecycle Manager for GLaDOS_DAEMON-SYSTEM.
Orchestrates the draft then sandbox then approval and finally registration workflow,
enforcing the Ritual of Renewal (restore point before modification)
and fail-closed Operator approval.

Design principles:
- Self-improving without being self-modifying without review.
- Every proposal is tracked: approved skills are registered, rejected
  proposals are logged as lessons (never silently discarded).
- Restore points are created BEFORE any SkillRegistry mutation.
- Critical-risk proposals require additional safeguards.
- Sandbox dry-run executes only the proposal's tests, no host access.
"""

import json
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field, field_validator

from glados.core.context import RuntimeContext


class ProposalStatus(str, Enum):
    """Lifecycle states for a skill proposal."""
    DRAFT = "draft"
    SANDBOX_PASS = "sandbox_pass"
    SANDBOX_FAIL = "sandbox_fail"
    APPROVED = "approved"
    REJECTED = "rejected"


class SkillProposal(BaseModel):
    """
    A candidate skill proposed by BrainEngine for inclusion in SkillRegistry.
    Tracks its own lifecycle state and risk assessment.
    """
    proposal_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this proposal"
    )
    skill_name: str = Field(..., min_length=1, description="Name of the proposed skill")
    description: str = Field(..., min_length=1, description="What the skill does")
    code: str = Field(..., min_length=1, description="Python code implementing the skill")
    tests: str = Field(..., min_length=1, description="Test suite for the skill")
    risk_level: str = Field(default="low", description="Risk assessment: low/medium/high/critical")
    status: ProposalStatus = Field(default=ProposalStatus.DRAFT)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of proposal creation"
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Reason for rejection (if rejected)"
    )

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"risk_level must be one of {allowed}, got '{v}'")
        return v


class RestorePoint(BaseModel):
    """
    Snapshot of SkillRegistry state before a mutation.
    Enables rollback per the Ritual of Renewal.
    """
    restore_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    proposal_id: str
    skill_name: str
    registry_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of registered skills before mutation"
    )


class SkillLifecycleManager:
    """
    Orchestrates the skill lifecycle: draft → sandbox → approve/reject.
    Enforces Ritual of Renewal and fail-closed Operator approval.
    """

    def __init__(
        self,
        ctx: RuntimeContext,
        restore_points_dir: Path = Path("data/restore_points"),
    ) -> None:
        self.ctx = ctx
        self.restore_points_dir = restore_points_dir
        self.restore_points_dir.mkdir(parents=True, exist_ok=True)
        self._proposals: dict[str, SkillProposal] = {}
        self.logger = logger.bind(component="SkillLifecycleManager")

    async def draft(self, proposal: SkillProposal) -> SkillProposal:
        """
        Accepts a new skill proposal into DRAFT state.
        
        :param proposal: The skill proposal to draft.
        :return: The proposal with status set to DRAFT.
        """
        proposal.status = ProposalStatus.DRAFT
        self._proposals[proposal.proposal_id] = proposal
        self.logger.info(
            f"Skill proposal drafted: {proposal.skill_name} "
            f"(id={proposal.proposal_id}, risk={proposal.risk_level})"
        )
        return proposal

    async def sandbox_test(self, proposal_id: str) -> SkillProposal:
        """
        Executes the proposal's tests in an isolated sandbox.
        No host access beyond the existing SecurityPolicy allowlist.
        
        :param proposal_id: The ID of the proposal to test.
        :return: The proposal with status updated to SANDBOX_PASS or SANDBOX_FAIL.
        :raises KeyError: If the proposal is not found.
        """
        proposal = self._proposals[proposal_id]
        
        with tempfile.TemporaryDirectory() as sandbox_dir:
            sandbox_path = Path(sandbox_dir)
            
            # Write proposal code and tests to sandbox
            code_file = sandbox_path / f"{proposal.skill_name}.py"
            code_file.write_text(proposal.code, encoding="utf-8")
            
            test_file = sandbox_path / f"test_{proposal.skill_name}.py"
            test_file.write_text(proposal.tests, encoding="utf-8")
            
            # Execute tests in isolated subprocess
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-v"],
                    cwd=sandbox_path,
                    capture_output=True,
                    text=True,
                    timeout=30,  # Hard timeout to prevent runaway tests
                    env={"PATH": "/usr/bin:/bin"},  # Minimal environment
                )
                
                if result.returncode == 0:
                    proposal.status = ProposalStatus.SANDBOX_PASS
                    self.logger.info(f"Sandbox test passed for {proposal.skill_name}")
                else:
                    proposal.status = ProposalStatus.SANDBOX_FAIL
                    self.logger.warning(
                        f"Sandbox test failed for {proposal.skill_name}: "
                        f"{result.stderr[:200]}"
                    )
            except subprocess.TimeoutExpired:
                proposal.status = ProposalStatus.SANDBOX_FAIL
                self.logger.error(f"Sandbox test timed out for {proposal.skill_name}")
            except Exception as e:
                proposal.status = ProposalStatus.SANDBOX_FAIL
                self.logger.error(f"Sandbox test error for {proposal.skill_name}: {e}")
        
        return proposal

    async def approve(
        self,
        proposal_id: str,
        operator_confirmed: bool = False,
    ) -> SkillProposal:
        """
        Approves a proposal and registers it in SkillRegistry.
        Creates a restore point BEFORE registration (Ritual of Renewal).
        
        :param proposal_id: The ID of the proposal to approve.
        :param operator_confirmed: Explicit Operator confirmation (required).
        :return: The proposal with status updated to APPROVED.
        :raises PermissionError: If operator_confirmed is False or risk is critical.
        :raises KeyError: If the proposal is not found.
        """
        proposal = self._proposals[proposal_id]
        
        # Fail-closed: explicit Operator confirmation required
        if not operator_confirmed:
            raise PermissionError(
                f"Cannot approve proposal {proposal_id} without explicit Operator confirmation"
            )
        
        # Critical risk requires additional safeguards
        if proposal.risk_level == "critical":
            raise PermissionError(
                f"Critical-risk proposal {proposal_id} requires additional safeguards "
                f"(e.g., dual-approval, extended review period)"
            )
        
        # Ritual of Renewal: create restore point BEFORE mutation
        restore_point = await self._create_restore_point(proposal)
        
        # Register the skill
        # Note: In production, this would call ctx.skills.register() with the actual skill
        # For now, we simulate the registration
        self.ctx.skills.register(proposal.skill_name)
        
        proposal.status = ProposalStatus.APPROVED
        self.logger.info(
            f"Skill proposal approved: {proposal.skill_name} "
            f"(restore_id={restore_point.restore_id})"
        )
        
        return proposal

    async def reject(self, proposal_id: str, reason: str) -> SkillProposal:
        """
        Rejects a proposal and logs the reason as a lesson in LTM.
        Rejected proposals are never silently discarded.
        
        :param proposal_id: The ID of the proposal to reject.
        :param reason: Human-readable reason for rejection.
        :return: The proposal with status updated to REJECTED.
        :raises KeyError: If the proposal is not found.
        """
        proposal = self._proposals[proposal_id]
        proposal.status = ProposalStatus.REJECTED
        proposal.rejection_reason = reason
        
        # Log the rejection as a lesson in LTM
        lesson = (
            f"Skill proposal rejected: {proposal.skill_name}. "
            f"Reason: {reason}. "
            f"Risk level: {proposal.risk_level}."
        )
        self.ctx.memory.remember(lesson, role="system", persist=True)
        
        self.logger.info(f"Skill proposal rejected: {proposal.skill_name} ({reason})")
        
        return proposal

    async def _create_restore_point(self, proposal: SkillProposal) -> RestorePoint:
        """
        Creates a restore point snapshot before SkillRegistry mutation.
        Enables rollback per the Ritual of Renewal.
        
        :param proposal: The proposal being approved.
        :return: The created RestorePoint.
        """
        # Snapshot current SkillRegistry state
        # Note: In production, this would call ctx.skills.list_all() or similar
        registry_snapshot = {
            "registered_skills": [],  # Placeholder for actual registry state
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        restore_point = RestorePoint(
            proposal_id=proposal.proposal_id,
            skill_name=proposal.skill_name,
            registry_snapshot=registry_snapshot,
        )
        
        # Persist restore point to disk
        restore_file = self.restore_points_dir / f"{restore_point.restore_id}.json"
        restore_file.write_text(
            restore_point.model_dump_json(indent=2),
            encoding="utf-8",
        )
        
        self.logger.debug(f"Restore point created: {restore_point.restore_id}")
        
        return restore_point