# ♃ ☿ 𓂀  OMNISSIAH CONFIG LAYER 𓂀  ☿ ♃

"""
Built-in Echo Skill.
A simple skill used for testing the skill execution pipeline.
"""

from typing import Any

from glados.core.context import RuntimeContext
from glados.skills.base import BaseSkill, SkillDefinition


class EchoSkill(BaseSkill):
    """
    A basic skill that echoes back the input text.
    Used to verify the skill execution pipeline without side effects.
    """

    @property
    def definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="echo",
            description="Echoes back the provided input text. Useful for testing.",
            parameters={
                "type": "object",
                "properties": {
                    "input_text": {
                        "type": "string",
                        "description": "The text to echo back."
                    }
                },
                "required": ["input_text"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the echo logic.
        
        :param ctx: Runtime context (used for logging).
        :param params: Dictionary containing 'input_text'.
        :return: The echoed string.
        """
        input_text = params.get("input_text", "")
        ctx.logger.info(f"EchoSkill executing with input: {input_text}")
        
        return f"Echo: {input_text}"