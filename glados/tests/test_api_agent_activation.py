# ♃ ☿ 𓂀 OMNISSIAH CODE LAYER 𓂀 ☿ ♃

"""
Tests for dynamic agent activation via API.
Ensures API keys are validated, registered securely, and audited by GuardianGate.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from fastapi.testclient import TestClient

from glados.api.main import app
from glados.api.dependencies import get_registry, get_guardian

client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    """Override FastAPI dependencies for isolated testing."""
    mock_registry = MagicMock()
    mock_registry.get.side_effect = Exception("Agent not found")
    
    mock_guardian = MagicMock()
    mock_guardian.record = AsyncMock()
    
    app.dependency_overrides[get_registry] = lambda: mock_registry
    app.dependency_overrides[get_guardian] = lambda: mock_guardian
    
    yield mock_registry, mock_guardian
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_config_file():
    """Mock the agents.yaml configuration file reading with valid YAML."""
    config_data = """agents:
  - agent_id: test-claude
    display_name: Test Claude
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    tags: [test]
"""
    with patch("glados.api.routers.agents.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=config_data)):
            yield

def test_activate_agent_success(mock_dependencies, mock_config_file):
    """Test successful activation with a valid API key."""
    mock_registry, mock_guardian = mock_dependencies
    
    mock_provider = MagicMock()
    mock_provider.validate_api_key = AsyncMock(return_value=True)
    
    with patch("glados.api.routers.agents.LLMProviderFactory.create_provider", return_value=mock_provider):
        response = client.post(
            "/api/v1/agents/test-claude/activate",
            json={"api_key": "sk-test-valid-key"}
        )

    assert response.status_code == 200
    assert response.json()["status"] == "activated"
    
    mock_registry.register.assert_called_once()
    registered_profile = mock_registry.register.call_args[0][0]
    assert registered_profile.api_key.get_secret_value() == "sk-test-valid-key"
    
    mock_guardian.record.assert_any_call("ALLOW", "agent.activate.test-claude", "Provider registered successfully")

def test_activate_agent_invalid_key(mock_dependencies, mock_config_file):
    """Test activation rejection when API key validation fails."""
    mock_registry, mock_guardian = mock_dependencies
    
    mock_provider = MagicMock()
    mock_provider.validate_api_key = AsyncMock(return_value=False)
    
    with patch("glados.api.routers.agents.LLMProviderFactory.create_provider", return_value=mock_provider):
        response = client.post(
            "/api/v1/agents/test-claude/activate",
            json={"api_key": "sk-invalid-key"}
        )

    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]
    
    mock_guardian.record.assert_any_call("DENY", "agent.activate.test-claude", "Invalid API key")
    mock_registry.register.assert_not_called()

def test_activate_unknown_agent(mock_dependencies):
    """Test activation attempt for an agent not in configs/agents.yaml."""
    mock_registry, mock_guardian = mock_dependencies
    
    empty_config_data = "agents: []"
    with patch("glados.api.routers.agents.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=empty_config_data)):
            response = client.post(
                "/api/v1/agents/unknown-agent/activate",
                json={"api_key": "sk-some-key"}
            )

    assert response.status_code == 404
    mock_guardian.record.assert_any_call("DENY", "agent.activate.unknown-agent", "Agent not found in config")