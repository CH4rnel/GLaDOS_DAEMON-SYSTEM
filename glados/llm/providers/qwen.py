# ♃ ☿  OMNISSIAH CODE LAYER  ☿ ♃

from glados.llm.providers.openai_compatible import OpenAICompatibleProvider
from glados.llm.models import AgentProfile

class QwenProvider(OpenAICompatibleProvider):
    """Qwen (DashScope) API provider - OpenAI-compatible endpoint."""
    
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    def __init__(self, profile: AgentProfile) -> None:
        super().__init__(profile)