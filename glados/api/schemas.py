# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Pydantic schemas for GLaDOS API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    agent_id: str
    session_id: Optional[str] = None


class ChatChunk(BaseModel):
    type: str  # "chunk" or "end"
    content: str


class AuditLogEntry(BaseModel):
    timestamp: str
    action: str
    status: str
    details: str