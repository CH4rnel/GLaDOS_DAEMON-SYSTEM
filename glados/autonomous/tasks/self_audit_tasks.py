# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Self-Audit Tasks for GLaDOS_DAEMON-SYSTEM.
Scheduled analysis tasks for dependency/CVE scanning and static analysis.
Results feed GuardianGate's audit log for Operator review.

Design principles:
- Self-audit as scheduled analysis, NOT autonomous self-patching.
- Uses existing autonomous/tasks/ infrastructure (same pattern as log_rotation_tasks.py).
- Dependency scan: pip-audit for CVE detection.
- Static analysis: ruff (already a dependency) + bandit for security-specific lint.
- All findings logged to GuardianGate audit log for transparency.
"""

import json
import subprocess
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext


class AuditReport(BaseModel):
    """
    Structured report from a self-audit task.
    Contains findings, severity levels, and actionable details.
    """
    task_name: str = Field(..., description="Name of the audit task (e.g., 'dependency_audit')")
    findings_count: int = Field(default=0, description="Total number of findings")
    critical_findings: int = Field(default=0, description="Number of critical-severity findings")
    details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed findings with severity, package/issue, and remediation info"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the audit run"
    )
    success: bool = Field(default=True, description="Whether the audit task completed successfully")


async def run_dependency_audit(ctx: RuntimeContext) -> AuditReport:
    """
    Runs pip-audit to scan for known CVEs in installed dependencies.
    
    :param ctx: Runtime context with logger access.
    :return: AuditReport with findings.
    """
    ctx.logger.info("Starting dependency audit (pip-audit)")
    
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute timeout
        )
        
        findings = []
        critical_count = 0
        
        if result.returncode != 0 and result.stdout:
            try:
                audit_data = json.loads(result.stdout)
                dependencies = audit_data.get("dependencies", [])
                
                for dep in dependencies:
                    vulns = dep.get("vulns", [])
                    for vuln in vulns:
                        severity = "medium"  # Default severity
                        if "critical" in vuln.get("id", "").lower():
                            severity = "critical"
                            critical_count += 1
                        
                        findings.append({
                            "severity": severity,
                            "package": dep.get("name"),
                            "version": dep.get("version"),
                            "cve": vuln.get("id"),
                            "fix_versions": vuln.get("fix_versions", []),
                        })
            except json.JSONDecodeError:
                ctx.logger.warning("Failed to parse pip-audit JSON output")
        
        report = AuditReport(
            task_name="dependency_audit",
            findings_count=len(findings),
            critical_findings=critical_count,
            details=findings,
        )
        
        ctx.logger.info(
            f"Dependency audit complete: {report.findings_count} findings "
            f"({report.critical_findings} critical)"
        )
        
        return report
        
    except subprocess.TimeoutExpired:
        ctx.logger.error("Dependency audit timed out after 120 seconds")
        return AuditReport(task_name="dependency_audit", success=False)
    except Exception as e:
        ctx.logger.error(f"Dependency audit failed: {e}", exc_info=True)
        return AuditReport(task_name="dependency_audit", success=False)


async def run_static_analysis(ctx: RuntimeContext) -> AuditReport:
    """
    Runs ruff and bandit for static analysis and security linting.
    
    :param ctx: Runtime context with logger access.
    :return: AuditReport with findings.
    """
    ctx.logger.info("Starting static analysis (ruff + bandit)")
    
    findings = []
    
    try:
        # Run ruff for general linting
        ruff_result = subprocess.run(
            ["ruff", "check", "--output-format", "json", "glados/"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if ruff_result.returncode != 0 and ruff_result.stdout:
            try:
                ruff_issues = json.loads(ruff_result.stdout)
                for issue in ruff_issues:
                    findings.append({
                        "tool": "ruff",
                        "severity": "low",
                        "file": issue.get("filename"),
                        "line": issue.get("location", {}).get("row"),
                        "code": issue.get("code"),
                        "message": issue.get("message"),
                    })
            except json.JSONDecodeError:
                ctx.logger.warning("Failed to parse ruff JSON output")
        
        # Run bandit for security-specific lint
        bandit_result = subprocess.run(
            ["bandit", "-r", "glados/", "-f", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if bandit_result.returncode != 0 and bandit_result.stdout:
            try:
                bandit_data = json.loads(bandit_result.stdout)
                for result in bandit_data.get("results", []):
                    severity = result.get("issue_severity", "low").lower()
                    if severity == "high":
                        severity = "critical"
                    
                    findings.append({
                        "tool": "bandit",
                        "severity": severity,
                        "file": result.get("filename"),
                        "line": result.get("line_number"),
                        "test_id": result.get("test_id"),
                        "message": result.get("issue_text"),
                    })
            except json.JSONDecodeError:
                ctx.logger.warning("Failed to parse bandit JSON output")
        
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        
        report = AuditReport(
            task_name="static_analysis",
            findings_count=len(findings),
            critical_findings=critical_count,
            details=findings,
        )
        
        ctx.logger.info(
            f"Static analysis complete: {report.findings_count} findings "
            f"({report.critical_findings} critical)"
        )
        
        return report
        
    except subprocess.TimeoutExpired:
        ctx.logger.error("Static analysis timed out after 60 seconds")
        return AuditReport(task_name="static_analysis", success=False)
    except Exception as e:
        ctx.logger.error(f"Static analysis failed: {e}", exc_info=True)
        return AuditReport(task_name="static_analysis", success=False)