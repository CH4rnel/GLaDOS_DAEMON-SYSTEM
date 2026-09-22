# ♃ ☿ 𓂀  OMNISSIAH CODE LAYER 𓂀  ☿ ♃

"""
Built-in Word Count Skill.
Counts the number of words in the provided text.
"""

from typing import Any

from glados.core.context import RuntimeContext
from glados.skills.base import BaseSkill, SkillDefinition


class WordCountSkill(BaseSkill):
    """
    A skill that counts the number of words in a given text.
    """

    @property
    def definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="word_count",
            description="Counts the number of words in the provided input text.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to count words in."
                    }
                },
                "required": ["text"]
            }
        )

    async def execute(self, ctx: RuntimeContext, params: dict[str, Any]) -> Any:
        """
        Executes the word counting logic.
        """
        text = params.get("text", "")
        ctx.logger.debug(f"WordCountSkill executing on text of length {len(text)}")
        
        if not text or not text.strip():
            return 0
        return len(text.split())