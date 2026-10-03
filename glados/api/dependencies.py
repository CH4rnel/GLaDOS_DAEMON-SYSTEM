# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

from fastapi import Request
from glados.llm.registry import LLMRegistry
from glados.security.guardian import GuardianGate
from glados.tools.registry import ToolRegistry

def get_registry(request: Request) -> LLMRegistry:
    return request.app.state.llm_registry

def get_guardian(request: Request) -> GuardianGate:
    return request.app.state.guardian_gate

def get_tool_registry(request: Request) -> ToolRegistry:
    return request.app.state.tool_registry