# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
REST router for retrieving GuardianGate audit logs.
"""

from fastapi import APIRouter, Query
from typing import List
from loguru import logger

from glados.api.schemas import AuditLogEntry
from glados.security.guardian import get_guardian_logs

router = APIRouter()

@router.get("/api/v1/audit", response_model=List[AuditLogEntry])
async def get_audit_logs(limit: int = Query(default=50, le=500)):
    """
    Retrieve recent GuardianGate audit logs for the monitoring dashboard.
    """
    logger.debug(f"Fetching audit logs with limit: {limit}")
    logs = get_guardian_logs(limit=limit)
    return logs