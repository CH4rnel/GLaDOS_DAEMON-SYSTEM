# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for LLM provider streaming support.
Covers complete_stream() async generator for Anthropic, OpenAI, and Ollama providers,
and WebSocket integration with the shared application state.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import SecretStr

from glados.llm.models import AgentProfile, ProviderType, LLMMessage
from glados.llm.providers.anthropic import AnthropicProvider
from glados.llm.providers.openai import OpenAIProvider
from glados.llm.providers.ollama import OllamaProvider


class TestAnthropicStreaming:
    """Tests for Anthropic provider streaming via messages.stream()."""

    @pytest.mark.asyncio
    async def test_complete_stream_yields_text_chunks(self):
        """Test that complete_stream yields text chunks from Anthropic SDK stream."""
        profile = AgentProfile(
            agent_id="claude-test",
            display_name="Claude Test",
            provider=ProviderType.ANTHROPIC,
            model="claude-sonnet-4-6",
            api_key=SecretStr("sk-ant-test"),
        )

        provider = AnthropicProvider(profile)

        class MockStreamContext:
            def __init__(self):
                async def mock_text_stream():
                    yield "Hello "
                    yield "world"
                self.text_stream = mock_text_stream()

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        with patch.object(provider, '_get_client') as mock_client:
            mock_client.return_value.messages.stream.return_value = MockStreamContext()

            chunks = []
            messages = [LLMMessage(role="user", content="Hi")]
            async for chunk in provider.complete_stream(messages, profile):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0] == "Hello "
        assert chunks[1] == "world"


class TestOpenAIStreaming:
    """Tests for OpenAI provider streaming (DeepSeek/Groq/Qwen compatible)."""

    @pytest.mark.asyncio
    async def test_complete_stream_yields_content_chunks(self):
        """Test that complete_stream yields content chunks from OpenAI stream."""
        profile = AgentProfile(
            agent_id="deepseek-test",
            display_name="DeepSeek Test",
            provider=ProviderType.DEEPSEEK,
            model="deepseek-chat",
            api_key=SecretStr("sk-ds-test"),
        )

        provider = OpenAIProvider(profile)

        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Hello "}}]}'
            yield 'data: {"choices": [{"delta": {"content": "world"}}]}'
            yield 'data: [DONE]'

        mock_response.aiter_lines = mock_aiter_lines

        class MockStreamContext:
            async def __aenter__(self):
                return mock_response
            async def __aexit__(self, *args):
                pass

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=MockStreamContext())

        with patch.object(provider, '_get_client', return_value=mock_client):
            chunks = []
            messages = [LLMMessage(role="user", content="Hi")]
            async for chunk in provider.complete_stream(messages, profile):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0] == "Hello "
        assert chunks[1] == "world"


class TestOllamaStreaming:
    """Tests for Ollama provider streaming via REST API."""

    @pytest.mark.asyncio
    async def test_complete_stream_yields_response_chunks(self):
        """Test that complete_stream yields response chunks from Ollama stream endpoint."""
        profile = AgentProfile(
            agent_id="ollama-test",
            display_name="Ollama Test",
            provider=ProviderType.OLLAMA,
            model="qwen2.5:7b",
            base_url="http://localhost:11434",
        )

        provider = OllamaProvider(profile)

        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_lines():
            yield '{"message":{"content":"Hello "},"done":false}'
            yield '{"message":{"content":"world"},"done":true}'

        mock_response.aiter_lines = mock_aiter_lines

        class MockStreamContext:
            async def __aenter__(self):
                return mock_response
            async def __aexit__(self, *args):
                pass

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=MockStreamContext())

        with patch.object(provider, '_get_client', return_value=mock_client):
            chunks = []
            messages = [LLMMessage(role="user", content="Hi")]
            async for chunk in provider.complete_stream(messages, profile):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0] == "Hello "
        assert chunks[1] == "world"


class TestWebSocketStreamingIntegration:
    """Tests for WebSocket chat endpoint with shared application state."""

    @pytest.mark.asyncio
    async def test_websocket_streams_real_llm_response(self):
        """Test that WebSocket endpoint streams real LLM response chunks via app.state."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from glados.api.routers.chat import router as chat_router
        from glados.llm.factory import LLMProviderFactory

        # Prepare mock data
        mock_profile = AgentProfile(
            agent_id="test-agent",
            display_name="Test Agent",
            provider=ProviderType.ANTHROPIC,
            model="claude-sonnet-4-6",
            api_key=SecretStr("sk-test"),
        )

        mock_provider = MagicMock()

        async def mock_complete_stream(messages, profile):
            yield "Hello "
            yield "from "
            yield "Claude"

        mock_provider.complete_stream = mock_complete_stream

        # Create isolated FastAPI app — bypasses global lifespan entirely
        test_app = FastAPI()
        test_app.include_router(chat_router)

        # Manually inject shared state
        mock_registry = MagicMock()
        mock_registry.get.return_value = mock_profile
        test_app.state.llm_registry = mock_registry

        # Patch the factory method on the class itself
        with patch.object(LLMProviderFactory, "create_provider", return_value=mock_provider):
            client = TestClient(test_app)

            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_json({"message": "Hi", "agent_id": "test-agent"})

                chunk_1 = websocket.receive_json()
                assert chunk_1["type"] == "chunk"
                assert chunk_1["content"] == "Hello "

                chunk_2 = websocket.receive_json()
                assert chunk_2["type"] == "chunk"
                assert chunk_2["content"] == "from "

                chunk_3 = websocket.receive_json()
                assert chunk_3["type"] == "chunk"
                assert chunk_3["content"] == "Claude"

                end = websocket.receive_json()
                assert end["type"] == "end"