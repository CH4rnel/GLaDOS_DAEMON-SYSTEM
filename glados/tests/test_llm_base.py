# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for the GLaDOS LLM Base Interfaces.
Follows TDD methodology (Red Phase) to define the abstract contracts.
"""

import pytest
from typing import Any

# These imports will fail initially (Red Phase)
from glados.llm.base import BaseLLMProvider
from glados.llm.models import LLMMessage, LLMResponse, AgentProfile, ProviderType


class TestBaseLLMProvider:
    """Tests for the BaseLLMProvider abstract contract."""

    def test_cannot_instantiate_base_provider(self):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider()  # type: ignore

    def test_subclass_must_implement_complete(self):
        """Test that a subclass must implement the 'complete' method."""
        class IncompleteProvider(BaseLLMProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore

    def test_valid_subclass_can_be_instantiated(self):
        """Test that a fully implemented subclass can be instantiated."""
        class MockProvider(BaseLLMProvider):
            async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
                return LLMResponse(
                    content="Mock response",
                    model="mock-model",
                    provider=ProviderType.CUSTOM
                )
            
            async def health_check(self, profile: AgentProfile) -> bool:
                return True

        provider = MockProvider()
        assert provider is not None

    def test_subclass_must_implement_health_check(self):
        """Test that a subclass must implement the 'health_check' method."""
        class MissingHealthCheckProvider(BaseLLMProvider):
            async def complete(self, messages: list[LLMMessage], profile: AgentProfile) -> LLMResponse:
                return LLMResponse(
                    content="Mock",
                    model="mock",
                    provider=ProviderType.CUSTOM
                )
            # health_check is NOT implemented

        with pytest.raises(TypeError):
            MissingHealthCheckProvider()  # type: ignore