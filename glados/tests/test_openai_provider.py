# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS OpenAI LLM Provider.
Follows TDD methodology (Red Phase) to define the contract for OpenAI API integration.
"""

import pytest
from unittest.mock import MagicMock, patch

from glados.llm.providers.openai import OpenAIProvider
from glados.llm.models import LLMMessage, LLMResponse, AgentProfile, ProviderType


class TestOpenAIProvider:
    """Tests for the OpenAIProvider implementation."""

    def test_provider_initialization(self):
        """Test that OpenAIProvider can be initialized."""
        provider = OpenAIProvider()
        assert provider is not None

    def test_provider_inherits_base(self):
        """Test that OpenAIProvider inherits from BaseLLMProvider."""
        from glados.llm.base import BaseLLMProvider
        provider = OpenAIProvider()
        assert isinstance(provider, BaseLLMProvider)

    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(self):
        """Test that complete() returns a valid LLMResponse on success."""
        provider = OpenAIProvider()
        
        profile = AgentProfile(
            agent_id="gpt4_turbo",
            display_name="GPT-4 Turbo",
            provider=ProviderType.OPENAI,
            model="gpt-4-turbo",
            api_key="sk-test-12345"
        )
        
        messages = [LLMMessage(role="user", content="Hello")]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "model": "gpt-4-turbo",
                "choices": [{"message": {"role": "assistant", "content": "Hello there!"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.complete(messages, profile)
            
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello there!"
            assert result.model == "gpt-4-turbo"
            assert result.provider == ProviderType.OPENAI
            assert result.usage["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_complete_missing_api_key_returns_error(self):
        """Test that complete() returns an error response if api_key is missing."""
        provider = OpenAIProvider()
        
        profile = AgentProfile(
            agent_id="no_key_agent",
            display_name="No Key Agent",
            provider=ProviderType.OPENAI,
            model="gpt-4",
            api_key=None
        )
        
        messages = [LLMMessage(role="user", content="Hello")]
        
        result = await provider.complete(messages, profile)
        
        assert result.is_error is True
        assert "api_key" in result.content.lower()

    @pytest.mark.asyncio
    async def test_complete_handles_api_error(self):
        """Test that complete() handles HTTP API errors gracefully."""
        provider = OpenAIProvider()
        
        profile = AgentProfile(
            agent_id="gpt4_turbo",
            display_name="GPT-4 Turbo",
            provider=ProviderType.OPENAI,
            model="gpt-4-turbo",
            api_key="sk-invalid"
        )
        
        messages = [LLMMessage(role="user", content="Hello")]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            import httpx
            mock_resp_obj = MagicMock()
            mock_resp_obj.status_code = 401
            mock_resp_obj.text = "Invalid API Key"
            
            mock_post.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_resp_obj
            )
            
            result = await provider.complete(messages, profile)
            
            assert result.is_error is True
            assert "401" in result.content

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test that health_check() returns True when OpenAI API is available."""
        provider = OpenAIProvider()
        
        profile = AgentProfile(
            agent_id="gpt4_turbo",
            display_name="GPT-4 Turbo",
            provider=ProviderType.OPENAI,
            model="gpt-4-turbo",
            api_key="sk-test-12345"
        )
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await provider.health_check(profile)
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test that health_check() returns False when API is unreachable."""
        provider = OpenAIProvider()
        
        profile = AgentProfile(
            agent_id="gpt4_turbo",
            display_name="GPT-4 Turbo",
            provider=ProviderType.OPENAI,
            model="gpt-4-turbo",
            api_key="sk-test-12345"
        )
        
        with patch('httpx.AsyncClient.get') as mock_get:
            import httpx
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            result = await provider.health_check(profile)
            assert result is False