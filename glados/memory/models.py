# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Data models for the GLaDOS Memory subsystem.
Defines the core contract for memory records stored in STM and LTM.
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """
    Represents a single memory record.
    Can be stored in short-term memory (context window) or persisted in long-term memory.
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the memory record."
    )
    content: str = Field(
        ...,
        min_length=1,
        description="The textual content of the memory."
    )
    role: Literal["system", "user", "assistant"] = Field(
        ...,
        description="The role of the message author (strictly validated)."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the record was created."
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary metadata (source, tags, confidence, etc.)."
    )
    embedding: list[float] | None = Field(
        default=None,
        description="Optional vector embedding for semantic search."
    )