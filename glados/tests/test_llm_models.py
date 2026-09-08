# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS LLM Data Models.
Follows TDD methodology (Red Phase) to define the contract for messages, responses, and agent profiles.
"""

import pytest
from pydantic import ValidationError

# These imports will fail initially (Red Phase)
from glados.llm.models import LLMMessage, LLMResponse, AgentProfile, ProviderType


class TestLLMMessage:
    """Tests for the LLMMessage Pydantic model."""

    def test_create_valid_user_message(self):
        """Test creating a valid user message."""
        msg = LLMMessage(role="user", content="Hello, GLaDOS!")
        assert msg.role == "user"
        assert msg.content == "Hello, GLaDOS!"

    def test_create_valid_system_message(self):
        """Test creating a valid system message."""
        msg = LLMMessage(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"

    def test_invalid_role_rejected(self):
        """Test that an invalid role raises ValidationError."""
        with pytest.raises(ValidationError):
            LLMMessage(role="invalid_role", content="Test")

    def test_empty_content_rejected(self):
        """Test that empty content is rejected."""
        with pytest.raises(ValidationError):
            LLMMessage(role="user", content="")


class TestLLMResponse:
    """Tests for the LLMResponse Pydantic model."""

    def test_create_valid_response(self):
        """Test creating a valid LLM response."""
        resp = LLMResponse(
            content="Task completed.",
            model="qwen2.5-coder",
            provider=ProviderType.OLLAMA,
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
        assert resp.content == "Task completed."
        assert resp.model == "qwen2.5-coder"
        assert resp.provider == ProviderType.OLLAMA
        assert resp.usage["prompt_tokens"] == 10

    def test_response_with_metadata(self):
        """Test creating a response with custom metadata."""
        resp = LLMResponse(
            content="Done.",
            model="gpt-4",
            provider=ProviderType.OPENAI,
            metadata={"finish_reason": "stop", "agent_id": "codex_1"}
        )
        assert resp.metadata["agent_id"] == "codex_1"

    def test_empty_content_rejected(self):
        """Test that empty response content is rejected."""
        with pytest.raises(ValidationError):
            LLMResponse(content="", model="test", provider=ProviderType.OLLAMA)


class TestAgentProfile:
    """Tests for the AgentProfile Pydantic model."""

    def test_create_ollama_profile(self):
        """Test creating a profile for a local Ollama agent."""
        profile = AgentProfile(
            agent_id="local_qwen",
            display_name="Local Qwen Coder",
            provider=ProviderType.OLLAMA,
            model="qwen2.5-coder:7b",
            base_url="http://localhost:11434"
        )
        assert profile.agent_id == "local_qwen"
        assert profile.provider == ProviderType.OLLAMA
        assert profile.api_key is None  # Ollama doesn't need it by default

    def test_create_openai_profile(self):
        """Test creating a profile for an OpenAI agent."""
        profile = AgentProfile(
            agent_id="gpt4_turbo",
            display_name="GPT-4 Turbo",
            provider=ProviderType.OPENAI,
            model="gpt-4-turbo-preview",
            api_key="sk-test-123"
        )
        assert profile.api_key == "sk-test-123"

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentProfile(
                agent_id="test",
                display_name="Test"
                # Missing provider and model
            )

    def test_custom_system_prompt(self):
        """Test assigning a custom system prompt to the profile."""
        profile = AgentProfile(
            agent_id="grok_agent",
            display_name="Grok",
            provider=ProviderType.XAI,
            model="grok-1",
            api_key="xai-test",
            system_prompt="You are Grok, a witty AI."
        )
        assert "witty" in profile.system_prompt