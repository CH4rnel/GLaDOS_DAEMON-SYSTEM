# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Ollama Embedding Provider implementation for GLaDOS_DAEMON-SYSTEM.
Provides local-first, private vector embeddings via Ollama's /api/embeddings endpoint.
"""

import httpx
from loguru import logger

from glados.llm.embeddings.base import BaseEmbeddingProvider


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Provider for generating embeddings using local Ollama models.
    Defaults to 'nomic-embed-text', a highly efficient and capable embedding model.
    """

    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434", timeout: float = 30.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger.bind(component="OllamaEmbeddingProvider")

    async def embed(self, text: str) -> list[float]:
        """
        Generates an embedding vector for the given text.
        
        :param text: The input text to embed.
        :return: A list of floats representing the embedding.
        :raises httpx.HTTPError: If the Ollama API request fails.
        """
        self.logger.debug(f"Generating embedding for text: {text[:50]}...")
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(
                "/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            
            return data["embedding"]