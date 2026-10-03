# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
REST router for retrieving GuardianGate audit logs.
"""

from fastapi import APIRouter, Query, Depends
from typing import List
from loguru import logger

from glados.api.dependencies import get_guardian
from glados.security.guardian import GuardianGate

router = APIRouter()

@router.get("/api/v1/audit")
async def get_audit_logs(
    limit: int = Query(default=50, le=500),
    guardian: GuardianGate = Depends(get_guardian)
) -> List[dict]:
    """
    Retrieve recent GuardianGate audit logs for the monitoring dashboard.
    Returns raw dicts to avoid Pydantic response validation errors.
    """
    logger.debug(f"Fetching audit logs with limit: {limit}")
    
    raw_logs = guardian.recent_log(limit=limit)
    
    adapted_logs = []
    for log in raw_logs:
        adapted_logs.append({
            "timestamp": log.get("timestamp", log.get("time", "")),
            "action": log.get("action", log.get("event", "UNKNOWN")),
            "status": log.get("status", "UNKNOWN"),
            "details": log.get("details", log.get("message", ""))
        })
        
    return adapted_logs