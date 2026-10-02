# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

from glados.llm.providers.openai_compatible import OpenAICompatibleProvider
from glados.llm.models import AgentProfile

class QwenProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    def __init__(self, profile: AgentProfile) -> None:
        super().__init__(profile)