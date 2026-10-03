# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""Mistral AI via OpenAI-compatible endpoint.
Free tier covers Mistral Small/Medium."""

from glados.llm.providers.openai_compatible import OpenAICompatibleProvider
from glados.llm.models import AgentProfile

class MistralProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
    
    def __init__(self, profile: AgentProfile) -> None:
        super().__init__(profile)