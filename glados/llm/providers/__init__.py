# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
LLM Providers package for GLaDOS_DAEMON-SYSTEM.
Contains implementations for various LLM providers (Ollama, OpenAI, etc.).
"""

from glados.llm.providers.ollama import OllamaProvider
from glados.llm.providers.openai import OpenAIProvider

__all__ = [
    "OllamaProvider",
    "OpenAIProvider",
]