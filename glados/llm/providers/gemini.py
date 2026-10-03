# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀  ♃

"""Google Gemini via OpenAI-compatible endpoint."""

from glados.llm.providers.openai_compatible import OpenAICompatibleProvider
from glados.llm.models import AgentProfile

class GeminiProvider(OpenAICompatibleProvider):
    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    def __init__(self, profile: AgentProfile) -> None:
        profile_with_prefix = profile.model_copy()
        if not profile.model.startswith("models/"):
            profile_with_prefix.model = f"models/{profile.model}"
        super().__init__(profile_with_prefix)