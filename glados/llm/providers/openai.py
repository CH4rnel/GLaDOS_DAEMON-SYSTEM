# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

from glados.llm.providers.openai_compatible import OpenAICompatibleProvider
from glados.llm.models import AgentProfile

class OpenAIProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, profile: AgentProfile) -> None:
        super().__init__(profile)