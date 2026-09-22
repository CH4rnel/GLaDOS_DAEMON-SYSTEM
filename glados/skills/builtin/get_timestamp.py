# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

"""
Built-in Get Timestamp Skill.
Returns the current system timestamp.
"""

from datetime import datetime, timezone
from typing import Any

from glados.core.context import RuntimeContext
from glados.skills.base import BaseSkill, SkillDefinition


class GetTimestampSkill(BaseSkill):
    """
    A skill that returns the current UTC timestamp.
    """

    @property
    def definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="get_timestamp",
            description="Returns the current UTC timestamp in ISO format.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the timestamp retrieval logic.
        """
        ctx.logger.debug("GetTimestampSkill executing.")
        return datetime.now(timezone.utc).isoformat()