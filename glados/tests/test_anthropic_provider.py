# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS Anthropic LLM Provider.
Follows TDD methodology to define the contract for Anthropic API integration.
"""

import pytest
from unittest.mock import MagicMock, patch
from pydantic import SecretStr

from glados.llm.providers.anthropic import AnthropicProvider
from glados.llm.models import LLMMessage, LLMResponse, AgentProfile, ProviderType


class TestAnthropicProvider:
    """Tests for the AnthropicProvider implementation."""

    def test_provider_initialization(self):
        """Test that AnthropicProvider can be initialized."""
        provider = AnthropicProvider()
        assert provider is not None

    def test_provider_inherits_base(self):
        """Test that AnthropicProvider inherits from BaseLLMProvider."""
        from glados.llm.base import BaseLLMProvider
        provider = AnthropicProvider()
        assert isinstance(provider, BaseLLMProvider)

    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(self):
        """Test that complete() returns a valid LLMResponse on success."""
        provider = AnthropicProvider()
        
        profile = AgentProfile(
            agent_id="claude_sonnet",
            display_name="Claude Sonnet",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=SecretStr("sk-ant-test-12345")
        )
        
        messages = [LLMMessage(role="user", content="Hello")]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "msg_123",
                "model": "claude-3-5-sonnet-20241022",
                "content": [{"type": "text", "text": "Hello there!"}],
                "usage": {"input_tokens": 10, "output_tokens": 5}
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.complete(messages, profile)
            
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello there!"
            assert result.model == "claude-3-5-sonnet-20241022"
            assert result.provider == ProviderType.ANTHROPIC

    @pytest.mark.asyncio
    async def test_complete_extracts_system_prompt(self):
        """Test that complete() extracts system prompt to separate field."""
        provider = AnthropicProvider()
        
        profile = AgentProfile(
            agent_id="claude_test",
            display_name="Claude Test",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=SecretStr("sk-ant-test")
        )
        
        messages = [
            LLMMessage(role="system", content="You are GLaDOS."),
            LLMMessage(role="user", content="Hello")
        ]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "Hello, test subject."}],
                "usage": {"input_tokens": 15, "output_tokens": 8}
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.complete(messages, profile)
            
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            
            assert request_data["system"] == "You are GLaDOS."
            assert len(request_data["messages"]) == 1
            assert request_data["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_complete_missing_api_key_returns_error(self):
        """Test that complete() returns an error response if api_key is missing."""
        provider = AnthropicProvider()
        
        profile = AgentProfile(
            agent_id="no_key_agent",
            display_name="No Key Agent",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=None
        )
        
        messages = [LLMMessage(role="user", content="Hello")]
        
        result = await provider.complete(messages, profile)
        
        assert result.is_error is True
        assert "api_key" in result.content.lower()

    @pytest.mark.asyncio
    async def test_complete_handles_api_error(self):
        """Test that complete() handles HTTP API errors gracefully."""
        provider = AnthropicProvider()
        
        profile = AgentProfile(
            agent_id="claude_test",
            display_name="Claude Test",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=SecretStr("sk-invalid")
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
        """Test that health_check() returns True when Anthropic API is available."""
        provider = AnthropicProvider()
        
        profile = AgentProfile(
            agent_id="claude_test",
            display_name="Claude Test",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=SecretStr("sk-ant-test")
        )
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await provider.health_check(profile)
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test that health_check() returns False when API is unreachable."""
        provider = AnthropicProvider()
        
        profile = AgentProfile(
            agent_id="claude_test",
            display_name="Claude Test",
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key=SecretStr("sk-ant-test")
        )
        
        with patch('httpx.AsyncClient.post') as mock_post:
            import httpx
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            
            result = await provider.health_check(profile)
            assert result is False