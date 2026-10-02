# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
REST router for the agent roster panel.
"""

from fastapi import APIRouter, Request
from typing import Any

router = APIRouter()


@router.get("/api/agents")
async def list_agents(request: Request) -> list[dict[str, Any]]:
    """Return all registered agent profiles for the roster panel."""
    registry = request.app.state.llm_registry
    return [p.model_dump(mode="json") for p in registry.list_all()]