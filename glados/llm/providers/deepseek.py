# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

from glados.llm.providers.openai_compatible import OpenAICompatibleProvider
from glados.llm.models import AgentProfile

class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek API provider - OpenAI-compatible endpoint."""
    
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    
    def __init__(self, profile: AgentProfile) -> None:
        super().__init__(profile)