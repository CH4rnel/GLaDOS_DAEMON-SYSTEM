# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Integration tests for API, Bootstrap, and Registry.
Uses mocking to isolate our logic from flaky external API networks.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from pydantic import SecretStr

from glados.api.main import app
from glados.llm.models import AgentProfile, ProviderType
from glados.llm.registry import LLMRegistry
from glados.security.guardian import GuardianGate

client = TestClient(app)

@pytest.fixture
def mock_registry():
    """Provide a clean registry for each test."""
    registry = LLMRegistry()
    app.state.llm_registry = registry
    return registry

@pytest.fixture
def mock_guardian():
    """Provide a clean guardian for each test."""
    guardian = MagicMock(spec=GuardianGate)
    guardian.log_audit = MagicMock()
    app.state.guardian_gate = guardian
    return guardian

@pytest.fixture
def temp_agents_yaml(tmp_path: Path):
    """Create a temporary agents.yaml for testing bootstrap logic."""
    yaml_content = """
agents:
  - agent_id: test-groq
    display_name: Test Groq
    provider: groq
    model: test-model
    api_key: ${GROQ_API_KEY}
  - agent_id: test-mistral
    display_name: Test Mistral
    provider: mistral
    model: test-model
    api_key: ${MISTRAL_API_KEY}
"""
    config_file = tmp_path / "agents.yaml"
    config_file.write_text(yaml_content)
    return config_file

def test_bootstrap_marks_missing_keys_as_inactive(temp_agents_yaml, mock_registry):
    """Test that agents without env vars are loaded but marked inactive."""
    # Ensure keys are NOT in environment
    with patch.dict(os.environ, {}, clear=True):
        from glados.core.bootstrap import AgentsBootstrap
        AgentsBootstrap.register_profiles(temp_agents_yaml, mock_registry)

    agents = mock_registry.list_all()
    assert len(agents) == 2
    
    # Both should be loaded, but inactive
    assert agents[0].agent_id == "test-groq"
    assert agents[0].is_active is False
    
    assert agents[1].agent_id == "test-mistral"
    assert agents[1].is_active is False

def test_bootstrap_activates_agents_with_valid_keys(temp_agents_yaml, mock_registry):
    """Test that agents with valid env vars are loaded and active."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "sk-test-123"}, clear=True):
        from glados.core.bootstrap import AgentsBootstrap
        AgentsBootstrap.register_profiles(temp_agents_yaml, mock_registry)

    agents = mock_registry.list_all()
    groq_agent = next(a for a in agents if a.agent_id == "test-groq")
    mistral_agent = next(a for a in agents if a.agent_id == "test-mistral")

    assert groq_agent.is_active is True
    assert mistral_agent.is_active is False

@patch('glados.api.routers.agents._load_all_agent_configs')
def test_list_agents_api_returns_correct_structure(mock_load_configs, mock_registry):
    """Test the /api/v1/agents endpoint returns the merged config/registry state."""
    # Mock the config loader to return our test agent
    mock_load_configs.return_value = [{
        "agent_id": "test-groq",
        "display_name": "Test Groq",
        "provider": "groq",
        "model": "test-model",
        "api_key": "${GROQ_API_KEY}",
        "tags": []
    }]
    
    # Pre-populate registry with one active agent
    profile = AgentProfile(
        agent_id="test-groq", 
        display_name="Test Groq", 
        provider=ProviderType.GROQ, 
        model="test-model",
        is_active=True
    )
    mock_registry.register(profile, provider=MagicMock())

    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    
    # Should contain our registered agent with is_active=True
    assert any(a["agent_id"] == "test-groq" and a["is_active"] is True for a in data)

@patch('glados.api.routers.agents.LLMProviderFactory.create_provider')
@patch('glados.api.routers.agents.yaml.safe_load')
def test_activate_agent_success(mock_yaml_load, mock_create_provider, mock_registry, mock_guardian, tmp_path):
    """Test successful agent activation via API."""
    # Mock the config file read
    mock_yaml_load.return_value = {
        "agents": [{
            "agent_id": "test-mistral",
            "display_name": "Test Mistral",
            "provider": "mistral",
            "model": "mistral-small",
            "tags": []
        }]
    }
    
    # Mock the provider and its validation
    mock_provider = MagicMock()
    mock_provider.validate_api_key = AsyncMock(return_value=True)
    mock_create_provider.return_value = mock_provider

    response = client.post(
        "/api/v1/agents/test-mistral/activate",
        json={"api_key": "sk-new-valid-key"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "activated"
    
    # Verify it was registered
    assert "test-mistral" in mock_registry._providers
    # Verify GuardianGate logged it
    mock_guardian.log_audit.assert_called_with("ALLOW", "agent.activate.test-mistral", "Provider registered successfully")

@patch('glados.api.routers.agents.LLMProviderFactory.create_provider')
@patch('glados.api.routers.agents.yaml.safe_load')
def test_activate_agent_invalid_key(mock_yaml_load, mock_create_provider, mock_registry, mock_guardian, tmp_path):
    """Test API rejects invalid API keys."""
    mock_yaml_load.return_value = {
        "agents": [{
            "agent_id": "test-mistral",
            "display_name": "Test Mistral",
            "provider": "mistral",
            "model": "mistral-small",
            "tags": []
        }]
    }
    
    mock_provider = MagicMock()
    mock_provider.validate_api_key = AsyncMock(return_value=False) # Simulate bad key
    mock_create_provider.return_value = mock_provider

    response = client.post(
        "/api/v1/agents/test-mistral/activate",
        json={"api_key": "sk-bad-key"}
    )

    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
    mock_guardian.log_audit.assert_called_with("DENY", "agent.activate.test-mistral", "Invalid API key")