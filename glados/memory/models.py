# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Memory models for GLaDOS_DAEMON-SYSTEM.
Defines the core data structures for memory records.
"""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """Represents a single unit of memory (a thought, fact, or message)."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    role: Literal["user", "assistant", "system"] = Field(..., description="Origin of the memory")
    content: str = Field(..., min_length=1, description="The actual content of the memory")
    metadata: dict = Field(default_factory=dict, description="Additional contextual metadata")