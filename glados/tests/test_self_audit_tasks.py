# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Self-Audit subsystem.
Ensures that dependency/CVE scans and static analysis run as scheduled tasks,
produce structured reports, and feed GuardianGate's audit log.
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from glados.autonomous.tasks.self_audit_tasks import (
    run_dependency_audit,
    run_static_analysis,
    AuditReport,
)
from glados.core.context import RuntimeContext


class TestAuditReport:
    """Tests for the AuditReport data model."""

    def test_report_creation_valid(self):
        """Test creating a valid audit report."""
        report = AuditReport(
            task_name="dependency_audit",
            findings_count=3,
            critical_findings=1,
            details=[
                {"severity": "critical", "package": "vulnerable-pkg", "cve": "CVE-2024-1234"},
                {"severity": "low", "package": "old-pkg", "cve": None},
                {"severity": "medium", "package": "another-pkg", "cve": "CVE-2024-5678"},
            ],
        )
        assert report.task_name == "dependency_audit"
        assert report.critical_findings == 1
        assert len(report.details) == 3

    def test_report_default_empty(self):
        """Test that AuditReport can be created with empty defaults."""
        report = AuditReport(task_name="test")
        assert report.findings_count == 0
        assert report.critical_findings == 0
        assert report.details == []


class TestSelfAuditTasks:
    """Tests for the self-audit scheduled tasks."""

    @pytest.fixture
    def mock_ctx(self):
        """Simulates RuntimeContext with security and logger."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.security = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.mark.asyncio
    async def test_dependency_audit_detects_vulnerabilities(self, mock_ctx):
        """Test that run_dependency_audit detects CVEs and reports them."""
        # Mock subprocess.run to simulate pip-audit output
        mock_result = MagicMock()
        mock_result.returncode = 1  # pip-audit returns 1 if vulnerabilities found
        mock_result.stdout = '{"dependencies": [{"name": "vulnerable-pkg", "version": "1.0.0", "vulns": [{"id": "CVE-2024-1234", "fix_versions": ["1.0.1"]}]}]}'
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            report = await run_dependency_audit(mock_ctx)
            
            assert report.task_name == "dependency_audit"
            assert report.findings_count >= 1
            assert any("CVE-2024-1234" in str(d) for d in report.details)

    @pytest.mark.asyncio
    async def test_dependency_audit_handles_no_vulnerabilities(self, mock_ctx):
        """Test that run_dependency_audit reports clean state when no CVEs found."""
        mock_result = MagicMock()
        mock_result.returncode = 0  # pip-audit returns 0 if clean
        mock_result.stdout = '{"dependencies": []}'
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            report = await run_dependency_audit(mock_ctx)
            
            assert report.findings_count == 0
            assert report.critical_findings == 0

    @pytest.mark.asyncio
    async def test_static_analysis_detects_security_issues(self, mock_ctx):
        """Test that run_static_analysis detects security issues via ruff/bandit."""
        # Mock subprocess.run to return JSON for both ruff and bandit
        ruff_result = MagicMock()
        ruff_result.returncode = 1  # Issues found
        ruff_result.stdout = json.dumps([
            {
                "filename": "test.py",
                "location": {"row": 10, "column": 5},
                "code": "B101",
                "message": "assert used",
            }
        ])
        ruff_result.stderr = ""
        
        bandit_result = MagicMock()
        bandit_result.returncode = 1  # Issues found
        bandit_result.stdout = json.dumps({
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 15,
                    "test_id": "B105",
                    "issue_text": "Possible hardcoded password",
                    "issue_severity": "HIGH",
                }
            ]
        })
        bandit_result.stderr = ""
        
        with patch("subprocess.run", side_effect=[ruff_result, bandit_result]):
            report = await run_static_analysis(mock_ctx)
            
            assert report.task_name == "static_analysis"
            assert report.findings_count >= 2  # At least 1 from ruff + 1 from bandit
            assert any(f.get("tool") == "ruff" for f in report.details)
            assert any(f.get("tool") == "bandit" for f in report.details)

    @pytest.mark.asyncio
    async def test_static_analysis_handles_clean_codebase(self, mock_ctx):
        """Test that run_static_analysis reports clean state when no issues found."""
        mock_result = MagicMock()
        mock_result.returncode = 0  # ruff/bandit returns 0 if clean
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            report = await run_static_analysis(mock_ctx)
            
            assert report.findings_count == 0

    @pytest.mark.asyncio
    async def test_audit_report_logged_to_guardian_gate(self, mock_ctx):
        """Test that audit reports are logged to GuardianGate's audit log."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        
        with patch("subprocess.run", return_value=mock_result):
            await run_dependency_audit(mock_ctx)
            
            # Verify logger was called with audit information
            mock_ctx.logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_audit_handles_subprocess_failure_gracefully(self, mock_ctx):
        """Test that audit tasks handle subprocess failures without crashing."""
        with patch("subprocess.run", side_effect=Exception("Subprocess failed")):
            report = await run_dependency_audit(mock_ctx)
            
            # Should return a report indicating failure, not raise
            assert report.task_name == "dependency_audit"
            assert report.findings_count == 0  # No findings if tool failed