# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
REST router for retrieving GuardianGate audit logs.
"""

from fastapi import APIRouter, Query, Request
from typing import List
from loguru import logger

from glados.api.schemas import AuditLogEntry

router = APIRouter()


@router.get("/api/v1/audit")
async def get_audit_logs(request: Request, limit: int = Query(default=50, le=500)) -> List[dict]:
    """
    Retrieve recent GuardianGate audit logs for the monitoring dashboard.
    Returns raw dicts to avoid Pydantic response validation errors if internal 
    log structure slightly differs from the API schema.
    """
    logger.debug(f"Fetching audit logs with limit: {limit}")
    guardian = request.app.state.guardian
    
    # Fetch raw logs from GuardianGate
    raw_logs = guardian.recent_log(limit=limit)
    
    # Adapt raw logs to match the expected API schema gracefully
    adapted_logs = []
    for log in raw_logs:
        adapted_logs.append({
            "timestamp": log.get("timestamp", log.get("time", "")),
            "action": log.get("action", log.get("event", "UNKNOWN")),
            "status": log.get("status", "UNKNOWN"),
            "details": log.get("details", log.get("message", ""))
        })
        
    return adapted_logs