# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
User Modeling subsystem for GLaDOS_DAEMON-SYSTEM.
Extracts durable user preferences from LTM, versions them, and stores locally.
Fully inspectable, editable, and erasable by the Operator (Codex Article V).

Design principles:
- Local-first: no hosted dependencies (Honcho, etc.) — memory belongs to the Operator.
- Versioned: each reflection increments the version, preserving history.
- Inspectable: stored as plain JSON, readable by the Operator at any time.
- Erasable: single function call removes all user model data (Right to Forget).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field

from glados.core.context import RuntimeContext


class UserModel(BaseModel):
    """
    Versioned model of the Operator's stable preferences and working style.
    Extracted periodically from LTM via LLM analysis.
    """
    version: int = Field(default=0, description="Monotonically increasing version number")
    stable_preferences: list[str] = Field(
        default_factory=list,
        description="Durable preferences (e.g., 'prefers TDD red-green-refactor')"
    )
    working_style: list[str] = Field(
        default_factory=list,
        description="Observed working patterns (e.g., 'code-first explanations')"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the last successful reflection"
    )


def save_user_model(model: UserModel, path: Path) -> None:
    """
    Persists the UserModel to disk as JSON.
    
    :param model: The UserModel to save.
    :param path: File path for storage.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    logger.debug(f"UserModel saved to {path} (version={model.version})")


def load_user_model(path: Path) -> Optional[UserModel]:
    """
    Loads the UserModel from disk.
    
    :param path: File path to load from.
    :return: The loaded UserModel, or None if the file does not exist.
    """
    if not path.exists():
        return None
    
    data = json.loads(path.read_text(encoding="utf-8"))
    return UserModel.model_validate(data)


def erase_user_model(path: Path) -> None:
    """
    Completely erases the UserModel from disk (Right to Forget).
    
    :param path: File path to erase.
    """
    if path.exists():
        path.unlink()
        logger.info(f"UserModel erased from {path}")


async def reflect_on_user(
    ctx: RuntimeContext,
    model_path: Path = Path("data/user_model.json"),
    days: int = 7
) -> Optional[UserModel]:
    """
    Periodic reflection task: reads recent LTM, asks the LLM to extract
    durable patterns, versions the result, and stores it locally.
    
    :param ctx: Runtime context with memory and brain access.
    :param model_path: Path to store the UserModel.
    :param days: Number of days of LTM to analyze.
    :return: The updated UserModel, or None if LTM was empty.
    """
    recent_records = ctx.memory.ltm.get_recent(days=days)
    
    if not recent_records:
        ctx.logger.debug("No recent LTM records for user reflection")
        return None
    
    # Build prompt for LLM analysis
    records_text = "\n".join(
        f"[{r.role}] {r.content}" for r in recent_records[:20]  # Limit to 20 records
    )
    
    prompt = f"""Analyze the following conversation history and extract the Operator's stable preferences and working style.
Return a JSON object with two fields:
- "stable_preferences": list of durable preferences (e.g., "prefers TDD", "likes concise responses")
- "working_style": list of observed working patterns (e.g., "code-first", "detailed explanations")

Conversation history:
{records_text}

Return ONLY the JSON object, no additional text."""
    
    try:
        from glados.llm.models import LLMMessage
        response = await ctx.brain.llm.complete(
            [LLMMessage(role="user", content=prompt)]
        )
        
        # Parse LLM response
        parsed = json.loads(response.content)
        
        # Load existing model to increment version
        existing = load_user_model(model_path)
        new_version = (existing.version + 1) if existing else 1
        
        new_model = UserModel(
            version=new_version,
            stable_preferences=parsed.get("stable_preferences", []),
            working_style=parsed.get("working_style", []),
            last_updated=datetime.now(timezone.utc)
        )
        
        save_user_model(new_model, model_path)
        ctx.logger.info(f"UserModel updated to version {new_version}")
        
        return new_model
        
    except Exception as e:
        ctx.logger.error(f"Failed to reflect on user: {e}", exc_info=True)
        return None