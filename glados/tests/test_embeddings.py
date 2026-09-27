# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Embedding subsystem.
Ensures that text can be converted to vector representations for semantic search.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from glados.llm.embeddings.ollama import OllamaEmbeddingProvider


class TestOllamaEmbeddingProvider:
    """Tests for the OllamaEmbeddingProvider implementation."""

    @pytest.fixture
    def provider(self):
        return OllamaEmbeddingProvider(model="nomic-embed-text", base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_embed_returns_vector_list(self, provider):
        """Test that embed() returns a list of floats on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3, 0.4]}
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient.post', return_value=mock_response) as mock_post:
            result = await provider.embed("Hello world")
            
            mock_post.assert_called_once_with(
                "/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": "Hello world"}
            )
            assert result == [0.1, 0.2, 0.3, 0.4]

    @pytest.mark.asyncio
    async def test_embed_handles_api_error(self, provider):
        """Test that embed() raises an exception on API failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await provider.embed("Hello world")