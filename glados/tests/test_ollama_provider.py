# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Ollama LLM Provider.
Follows TDD methodology (Red Phase) to define the contract for Ollama integration.
"""

import pytest
from unittest.mock import AsyncMock, patch

from glados.llm.providers.ollama import OllamaProvider
from glados.llm.models import LLMMessage, LLMResponse, AgentProfile, ProviderType


class TestOllamaProvider:
    """Tests for the OllamaProvider implementation."""

    def test_provider_initialization(self):
        """Test that OllamaProvider can be initialized."""
        provider = OllamaProvider()
        assert provider is not None

    def test_provider_inherits_base(self):
        """Test that OllamaProvider inherits from BaseLLMProvider."""
        from glados.llm.base import BaseLLMProvider
        provider = OllamaProvider()
        assert isinstance(provider, BaseLLMProvider)

    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(self):
        """Test that complete() returns a valid LLMResponse."""
        provider = OllamaProvider()
        
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="llama3.2:latest",
            base_url="http://localhost:11434"
        )
        
        messages = [
            LLMMessage(role="user", content="Hello")
        ]
        
        # Mock the HTTP request
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "model": "llama3.2:latest",
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?"
                },
                "done": True
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.complete(messages, profile)
            
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello! How can I help you?"
            assert result.model == "llama3.2:latest"
            assert result.provider == ProviderType.OLLAMA

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self):
        """Test that complete() correctly handles system messages."""
        provider = OllamaProvider()
        
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="llama3.2:latest",
            base_url="http://localhost:11434",
            system_prompt="You are a helpful assistant."
        )
        
        messages = [
            LLMMessage(role="user", content="What is 2+2?")
        ]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "model": "llama3.2:latest",
                "message": {
                    "role": "assistant",
                    "content": "4"
                },
                "done": True
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.complete(messages, profile)
            
            assert result.content == "4"
            
            # Verify that system prompt was included in the request
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            assert any(msg['role'] == 'system' for msg in request_data['messages'])

    @pytest.mark.asyncio
    async def test_complete_handles_api_error(self):
        """Test that complete() handles API errors gracefully."""
        provider = OllamaProvider()
        
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="nonexistent-model",
            base_url="http://localhost:11434"
        )
        
        messages = [
            LLMMessage(role="user", content="Test")
        ]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            import httpx
            mock_post.side_effect = httpx.HTTPStatusError(
                "Model not found",
                request=AsyncMock(),
                response=AsyncMock(status_code=404)
            )
            
            result = await provider.complete(messages, profile)
            
            assert result.is_error is True
            assert "error" in result.metadata

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test that health_check() returns True when Ollama is available."""
        provider = OllamaProvider()
        
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="llama3.2:latest",
            base_url="http://localhost:11434"
        )
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await provider.health_check(profile)
            
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test that health_check() returns False when Ollama is unavailable."""
        provider = OllamaProvider()
        
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="llama3.2:latest",
            base_url="http://localhost:9999"  # Wrong port
        )
        
        with patch('httpx.AsyncClient.get') as mock_get:
            import httpx
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            result = await provider.health_check(profile)
            
            assert result is False

    @pytest.mark.asyncio
    async def test_complete_with_conversation_history(self):
        """Test that complete() correctly handles multi-turn conversations."""
        provider = OllamaProvider()
        
        profile = AgentProfile(
            agent_id="test_ollama",
            display_name="Test Ollama",
            provider=ProviderType.OLLAMA,
            model="llama3.2:latest",
            base_url="http://localhost:11434"
        )
        
        messages = [
            LLMMessage(role="user", content="My name is Alice"),
            LLMMessage(role="assistant", content="Hello Alice!"),
            LLMMessage(role="user", content="What is my name?")
        ]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "model": "llama3.2:latest",
                "message": {
                    "role": "assistant",
                    "content": "Your name is Alice."
                },
                "done": True
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.complete(messages, profile)
            
            assert result.content == "Your name is Alice."
            
            # Verify all messages were sent
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            assert len(request_data['messages']) == 3