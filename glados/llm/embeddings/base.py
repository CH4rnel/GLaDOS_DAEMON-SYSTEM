# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Base interfaces for the GLaDOS Embedding subsystem.
"""

from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for all embedding provider implementations.
    """

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Converts a string of text into a dense vector representation.
        
        :param text: The input text to embed.
        :return: A list of floats representing the embedding vector.
        """
        pass